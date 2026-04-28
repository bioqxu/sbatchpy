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

---

## 🧠 Why sbatchpy?

Traditional SLURM scripting relies on string-based options:

```python
{"cpus-per-task": "4"}  # error-prone
```

With `sbatchpy`, you get:

```python
JobConfig(cpus_per_task=4)  # typed, safe, autocompleted
```

---

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

## 🧩 Presets

Use predefined resource configurations:

```python
job_id = client.submit(
    config=config,
    code="python script.py",
    preset="gpu_debug",
)
```

### Built-in presets

| Name         | Description      |
| ------------ | ---------------- |
| `cpu_shared` | Shared CPU queue |
| `gpu_debug`  | Short GPU jobs   |

---

## 📂 Job Scripts

By default, scripts are written to:

```bash
./.job/
```

You can customize:

```python
client = SBatchClient(job_directory="jobs/")
```

---

## 📊 Monitor Jobs

```python
jobs = client.list_jobs()

for job in jobs:
    print(job["id"], job["status"], job["name"])
```

---

## 🧱 Project Structure

```bash
sbatchpy/
├── core.py
├── __init__.py
├── pyproject.toml
└── README.md
```

---

## 🔧 Design Principles

* **Typed over dynamic** → fewer runtime errors
* **Minimal abstraction** → stay close to SLURM
* **Composable** → easy to extend for workflows

---

## ⚠️ Limitations

* Not a workflow manager (see Snakemake / Nextflow)
* No built-in dependency graph
* No job retry or scheduling logic (yet)

---

## 🚧 Roadmap

* [ ] YAML/JSON job configs
* [ ] Parameter sweeps (`map`)
* [ ] Job dependency support
* [ ] CLI (`sbatchpy submit config.yaml`)
* [ ] Logging and experiment tracking

---

## 🤝 Contributing

PRs and issues are welcome!

---

## 📄 License

MIT License

---

If you want, I can next:

* generate a **`pyproject.toml`** (ready for PyPI)
* add a **CLI interface**
* or write a **`map()` API for parameter sweeps** (very useful for your HPC workflows)
