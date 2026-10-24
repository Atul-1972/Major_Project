# Dependency policy

Phase 1 has no third-party Python dependencies. The reusable environment checker and checkpoint utility run with the standard library.

Use a repository-local virtual environment instead of the globally installed packages. Separate ML, backend, and test manifests will be added with their implementations. Installation success, import checks, and `pip check` must be recorded before calling any dependency set tested.

For the ML phase, a documented candidate pair is `torch==2.9.1` and `torchvision==0.24.1`; this is a reproducibility candidate, not a claim that it is the newest release or an installed/tested environment. The pair appears in the [official previous-version instructions](https://pytorch.org/get-started/previous-versions/) and supports this repository's Python 3.11 development target according to the [Torchvision compatibility table](https://github.com/pytorch/vision).

Recheck maintained versions and the actual Colab Python/CUDA runtime before pinning/installing. Do not downgrade or replace Colab's installed PyTorch blindly, and do not mix unrelated torch/torchvision versions. Record package versions, runtime hardware, and a lock/freeze with each experiment. CPU inference and Colab GPU training may need different wheel indexes while retaining compatible library versions.
