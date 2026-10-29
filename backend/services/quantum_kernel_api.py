from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/quantum-kernel",
    tags=["Quantum Kernel Lab"],
)


class KernelDemoRequest(BaseModel):
    task: str = Field(default="classification")
    landmarks: int = Field(default=4, ge=2, le=6)
    seed: int = Field(default=42, ge=0, le=100000)


@router.post("/demo")
def quantum_kernel_demo(request: KernelDemoRequest):
    try:
        from backend.services.quantum_kernel import run_quantum_kernel_demo

        return run_quantum_kernel_demo(
            task=request.task,
            landmarks=request.landmarks,
            seed=request.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Keep implementation details out of the API error response.
        raise HTTPException(
            status_code=500,
            detail="Quantum kernel demonstration failed.",
        ) from exc
