"""
RTS stage 1 — state step on GPU (torch, ADMM) instead of SCS: only it scales up to d = 6, 8.
Step problem: max ⟨G, ω⟩ subject to ω ⪰ 0 and ω ∈ L, where L is an affine set:
  Δ-step: L = {ω₁⊗ω₂ + Δ}, Δ ∈ Anti(A⊗B1)⊗Anti(B2⊗C) with zero marginals (⇒ ISO and operational independence exact);
  w-step: L = {V⊗ω₂ + Δ} (or {ω₁⊗V + Δ}), V symmetric with ISO marginals.
ADMM: X ← Π_PSD(Z − U + G/ρ) (eigh on GPU), Z ← Π_L(X + U), U ← U + X − Z.

The projections are exact and in closed form:
- Π onto Anti⊗Anti: ¼(X − X^{T1} − X^{T2} + X^{T1T2}), T1, T2 — partial transposes of the blocks;
- zero marginals inside Anti⊗Anti: the images of the adjoint maps {Y⊗I_B} and {I_AC⊗Z} are **orthogonal**
  (antisymmetric matrices are traceless), so it suffices to subtract both components separately;
- Π onto {V⊗ω₂ + Δ}: V ↦ ⟨ω₂, ·⟩/‖ω₂‖² componentwise (V ↦ V⊗ω₂ is an isometry up to a factor),
  then the affine projection of V onto the ISO marginals.

Numbers from this solver enter the report only after calibration against SCS on shared points (`rts_gpu_calib.py`).
"""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = torch.float64


def _t(x):
    return torch.as_tensor(np.ascontiguousarray(np.asarray(x, dtype=float)), device=DEV, dtype=DT)


class GState:
    def __init__(self, dims):
        self.dims = dims
        dA, dB1, dB2, dC = dims
        self.n1, self.n2 = dA * dB1, dB2 * dC
        self.N = self.n1 * self.n2
        self.eA, self.eB1 = torch.eye(dA, device=DEV, dtype=DT), torch.eye(dB1, device=DEV, dtype=DT)
        self.eB2, self.eC = torch.eye(dB2, device=DEV, dtype=DT), torch.eye(dC, device=DEV, dtype=DT)
        self.eN = torch.eye(self.N, device=DEV, dtype=DT)

    # ---------------- projections
    def proj_anti(self, X):
        n1, n2 = self.n1, self.n2
        T = X.reshape(n1, n2, n1, n2)
        out = 0.25 * (T - T.permute(2, 1, 0, 3) - T.permute(0, 3, 2, 1) + T.permute(2, 3, 0, 1))
        return out.reshape(self.N, self.N)

    def marginals(self, X):
        dA, dB1, dB2, dC = self.dims
        T = X.reshape(dA, dB1, dB2, dC, dA, dB1, dB2, dC)
        return torch.einsum("abcdebcf->adef", T), torch.einsum("abcdafgd->bcfg", T)

    def proj_delta(self, X):
        """Π onto {Δ ∈ Anti⊗Anti, both marginals zero}."""
        dA, dB1, dB2, dC = self.dims
        D = self.proj_anti(0.5 * (X + X.T))
        mAC, mB = self.marginals(D)
        c1 = torch.einsum("adeh,bf,cg->abcdefgh", mAC, self.eB1, self.eB2) / (dB1 * dB2)
        c2 = torch.einsum("bcfg,ae,dh->abcdefgh", mB, self.eA, self.eC) / (dA * dC)
        return D - (c1 + c2).reshape(self.N, self.N)

    def fix_local(self, V, d1, d2):
        """Affine projection: both marginals of V → I/d, trace 1."""
        V = 0.5 * (V + V.T)
        T = V.reshape(d1, d2, d1, d2)
        m1 = torch.einsum("ajbj->ab", T) - torch.eye(d1, device=DEV, dtype=DT) / d1
        m2 = torch.einsum("jajb->ab", T) - torch.eye(d2, device=DEV, dtype=DT) / d2
        tr = torch.trace(V) - 1
        return (V - torch.kron(m1, torch.eye(d2, device=DEV, dtype=DT)) / d2
                - torch.kron(torch.eye(d1, device=DEV, dtype=DT), m2) / d1
                + tr * torch.eye(d1 * d2, device=DEV, dtype=DT) / (d1 * d2))

    def proj_L(self, M, part, w1, w2, D):
        """Π onto the affine set of the step; returns (ω, parameter)."""
        dA, dB1, dB2, dC = self.dims
        if part == "D":
            Dn = self.proj_delta(M - torch.kron(w1, w2))
            return torch.kron(w1, w2) + Dn, Dn
        R = (M - D).reshape(self.n1, self.n2, self.n1, self.n2)
        if part == "w1":
            V = torch.einsum("apbq,pq->ab", R, w2) / (w2 * w2).sum()
            V = self.fix_local(V, dA, dB1)
            return torch.kron(V, w2) + D, V
        V = torch.einsum("apbq,ab->pq", R, w1) / (w1 * w1).sum()
        V = self.fix_local(V, dB2, dC)
        return torch.kron(w1, V) + D, V


EIGH_STATS = {"gpu": 0, "cpu_fallback": 0}


def _eigh(Y):
    """cuSOLVER sometimes fails to converge on degenerate spectra (error 34) — then compute on CPU (LAPACK)."""
    try:
        ev, evec = torch.linalg.eigh(Y)
        EIGH_STATS["gpu"] += 1
        return ev, evec
    except torch._C._LinAlgError:
        EIGH_STATS["cpu_fallback"] += 1
        ev, evec = torch.linalg.eigh(Y.cpu())
        return ev.to(Y.device), evec.to(Y.device)


def admm_step(gs, G, part, w1, w2, D, iters=400, rho=None, tol=1e-9, X=None, U=None, adapt=True):
    """max ⟨G, ω⟩ over ω ⪰ 0, ω ∈ L. Returns (parameter, ω, residuals, state for a warm start).
    adapt: balancing of ρ by the residuals (Boyd §3.4.1) — without it, at N = 1296 the residual infeasibility
    eats up to 0.4 units of 𝒯 in the cleanup."""
    Gt = 0.5 * (G + G.T)
    rho = rho or float(Gt.abs().max()) * 10
    Z, param = gs.proj_L(torch.kron(w1, w2) + D, part, w1, w2, D)
    X = Z.clone() if X is None else X
    U = torch.zeros_like(Z) if U is None else U
    pr = dr = float("nan")
    for k in range(iters):
        Y = Z - U + Gt / rho
        Y = 0.5 * (Y + Y.T)
        ev, evec = _eigh(Y)
        Xn = (evec * ev.clamp(min=0)) @ evec.T
        Zn, param = gs.proj_L(Xn + U, part, w1, w2, D)
        U = U + Xn - Zn
        pr = float((Xn - Zn).norm())
        dr = float(rho * (Zn - Z).norm())
        X, Z = Xn, Zn
        if pr < tol and dr < tol:
            break
        if adapt and (k + 1) % 25 == 0:
            if pr > 10 * dr:
                rho, U = rho * 2, U / 2
            elif dr > 10 * pr:
                rho, U = rho / 2, U * 2
    return param, Z, {"primal_res": pr, "dual_res": dr, "iters": k + 1, "rho": rho,
                      "eigh": dict(EIGH_STATS)}, (X, U)
