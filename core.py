from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


# -----------------------------
# Job configuration (typed)
# -----------------------------
@dataclass
class JobConfig:
    """
    Strongly-typed SLURM job configuration.
    """

    job_name: str
    time: str = "01:00:00"
    partition: Optional[str] = None
    nodes: int = 1
    cpus_per_task: int = 1
    ntasks_per_node: Optional[int] = None
    gpus: Optional[int] = None
    output: Optional[str] = None

    # allow extra sbatch args if needed
    extra: Dict[str, str] = field(default_factory=dict)

    def to_sbatch_dict(self) -> Dict[str, str]:
        """
        Convert dataclass fields into SBATCH-compatible dict.
        """
        mapping = {
            "job_name": "job-name",
            "cpus_per_task": "cpus-per-task",
            "ntasks_per_node": "ntasks-per-node",
        }

        result: Dict[str, str] = {}

        for key, value in asdict(self).items():
            if value is None or key == "extra":
                continue

            sbatch_key = mapping.get(key, key.replace("_", "-"))
            result[sbatch_key] = str(value)

        # merge extra args (highest priority)
        result.update(self.extra)

        return result


# -----------------------------
# Client
# -----------------------------
class SBatchClient:
    """
    SLURM sbatch client with typed configuration.
    """

    DEFAULT_PRESETS: Dict[str, Dict[str, str]] = {
        "cpu_shared": {
            "partition": "shared",
            "time": "01:00:00",
            "nodes": "1",
            "cpus-per-task": "5",
            "ntasks-per-node": "1",
        },
        "gpu_debug": {
            "partition": "gpu-debug",
            "gpus": "1",
            "cpus-per-task": "5",
            "time": "00:30:00",
            "nodes": "1",
        },
    }

    def __init__(
        self,
        job_directory: Optional[str | Path] = None,
        presets: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        self.job_dir = Path(job_directory or Path.cwd() / ".job")
        self.job_dir.mkdir(parents=True, exist_ok=True)

        self.presets = presets or self.DEFAULT_PRESETS.copy()

    # -----------------------------
    # Presets
    # -----------------------------
    def get_preset(self, name: str) -> Dict[str, str]:
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found.")
        return self.presets[name].copy()

    # -----------------------------
    # Script creation
    # -----------------------------
    def _write_directive(self, fh, key: str, value: str) -> None:
        fh.write(f"#SBATCH --{key}={value}\n")

    def _create_script(
        self,
        config: JobConfig,
        code: str,
        preset: Optional[str] = None,
    ) -> Path:
        """
        Create sbatch script file.
        """
        options = {}

        if preset:
            options.update(self.get_preset(preset))

        options.update(config.to_sbatch_dict())

        job_file = self.job_dir / config.job_name

        with job_file.open("w") as fh:
            fh.write("#!/bin/bash\n")
            fh.write("#SBATCH --no-requeue\n")

            for key, value in options.items():
                self._write_directive(fh, key, value)

            fh.write("\n")
            fh.write(code.strip() + "\n")

        return job_file

    # -----------------------------
    # Submission
    # -----------------------------
    def _submit(self, job_file: Path) -> str:
        result = subprocess.run(
            ["sbatch", str(job_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def submit(
        self,
        config: JobConfig,
        code: str,
        preset: Optional[str] = None,
        check_output_dir: bool = True,
        cleanup: bool = False,
    ) -> str:
        """
        Submit a job using typed configuration.
        """
        if config.output and check_output_dir:
            out_dir = Path(config.output).parent
            if out_dir and not out_dir.exists():
                raise FileNotFoundError(f"Output directory does not exist: {out_dir}")

        job_file = self._create_script(config, code, preset)
        job_id = self._submit(job_file)

        if cleanup:
            shutil.rmtree(self.job_dir, ignore_errors=True)

        return job_id

    # -----------------------------
    # Monitoring
    # -----------------------------
    def list_jobs(self) -> List[Dict[str, str]]:
        cmd = [
            "squeue",
            "--me",
            "--states=R,PD",
            "--format=%i|%j|%T|%M|%R",
            "--noheader",
        ]

        try:
            output = subprocess.check_output(cmd, text=True)
        except subprocess.CalledProcessError:
            return []

        jobs = []
        for line in output.strip().splitlines():
            job_id, name, status, runtime, info = line.split("|")
            jobs.append(
                {
                    "id": job_id,
                    "name": name,
                    "status": status,
                    "time": runtime,
                    "info": info,
                }
            )

        return jobs

    # -----------------------------
    # Cancellation
    # -----------------------------
    def cancel(self, job_id: str) -> None:
        """
        Cancel a single job.

        Args:
            job_id: SLURM job ID.
        """
        subprocess.run(
            ["scancel", job_id],
            check=True,
        )

    def cancel_many(self, job_ids: List[str]) -> None:
        """
        Cancel multiple jobs.

        Args:
            job_ids: List of SLURM job IDs.
        """
        if not job_ids:
            return

        subprocess.run(
            ["scancel", *job_ids],
            check=True,
        )

    def cancel_by_name(self, job_name: str) -> List[str]:
        """
        Cancel all jobs matching a given job name.

        Args:
            job_name: Name of the job.

        Returns:
            List of cancelled job IDs.
        """
        jobs = self.list_jobs()
        matched_ids = [job["id"] for job in jobs if job["name"] == job_name]

        if matched_ids:
            self.cancel_many(matched_ids)

        return matched_ids

    def cancel_all(self) -> List[str]:
        """
        Cancel ALL running/pending jobs for the current user.

        Returns:
            List of cancelled job IDs.
        """
        jobs = self.list_jobs()
        job_ids = [job["id"] for job in jobs]

        if job_ids:
            self.cancel_many(job_ids)

        return job_ids
        