# sbatchpy

A lightweight, typed Python interface for creating and submitting SLURM `sbatch` jobs.

`sbatchpy` replaces fragile dictionary-based job definitions with a clean, **dataclass-driven API**, making your HPC workflows safer, more readable, and easier to scale.

---

## ✨ Features

* ✅ Fully typed job configuration (`dataclass`)
* ✅ Simple job submission API
* ✅ Built-in presets for common workloads
* ✅ Safe subprocess handling (no `os.system`)
* ✅ Automatic script generation
* ✅ Lightweight and dependency-free

---

## 📦 Installation

```bash
pip install sbatchpy
```

Or install from source:

```bash
git clone https://github.com/bioqxu/sbatchpy.git
cd sbatchpy
pip install -e .
```

---

## 🚀 Quick Start

```python
from sbatchpy import SBatchClient, JobConfig

client = SBatchClient()

config = JobConfig(
    job_name="test_job",
    partition="cpu",
    cpus_per_task=4,
    time="00:30:00",
    output="logs/test.out",
)

job_id = client.submit(
    config=config,
    code="""
    module load python
    python script.py
    """,
)

print(job_id)
```

## ⚙️ Job Configuration

### Basic fields

```python
JobConfig(
    job_name="example",
    time="01:00:00",
    partition="gpu",
    nodes=1,
    cpus_per_task=8,
    gpus=1,
    output="logs/job.out",
)
```

### Advanced options

For unsupported SLURM flags:

```python
JobConfig(
    job_name="advanced",
    extra={
        "constraint": "A100",
        "mem": "32G",
    },
)
```

---

## 📊 Monitor Jobs

```python
jobs = client.list_jobs()

for job in jobs:
    print(job["id"], job["status"], job["name"])
```
---

## 🛑 Cancel Jobs

Safely cancel SLURM jobs. Bulk actions require confirmation.

### Single job

```python
client.cancel("123456")
```

### Multiple jobs

```python
client.cancel_many(["123", "124"], confirm=True)
```

### By name

```python
client.cancel_by_name("rna_seq_job", confirm=True, interactive=True)
```

### All jobs ⚠️

```python
client.cancel_all(confirm=True, interactive=True)
```

---

### 🔒 Safety

* `confirm=True` → required for bulk cancel
* `interactive=True` → optional prompt

Without confirmation:

```python
client.cancel_all()
```

→ raises an error

---

Only running (`R`) and pending (`PD`) jobs are affected.

---

## 📄 License

MIT License

