from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class SBatchClient:
    """
    High-level interface for creating and submitting SLURM sbatch jobs.
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
        """
        Args:
            job_directory: Directory where sbatch scripts are stored.
            presets: Optional custom presets overriding defaults.
        """
        self.job_dir = Path(job_directory or Path.cwd() / ".job")
        self.job_dir.mkdir(parents=True, exist_ok=True)

        self.presets = presets or self.DEFAULT_PRESETS.copy()

    # -----------------------------
    # Presets
    # -----------------------------
    def get_preset(self, name: str) -> Dict[str, str]:
        """Return a preset configuration."""
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
        options: Dict[str, str],
        code: str,
        preset: Optional[str] = None,
    ) -> Path:
        """
        Generate an sbatch script file.

        Returns:
            Path to script.
        """
        merged = {}

        if preset:
            merged.update(self.get_preset(preset))

        merged.update(options)

        if "job-name" not in merged:
            raise ValueError("Missing required option: 'job-name'")

        job_file = self.job_dir / merged["job-name"]

        with job_file.open("w") as fh:
            fh.write("#!/bin/bash\n")
            fh.write("#SBATCH --no-requeue\n")

            for key, value in merged.items():
                self._write_directive(fh, key, value)

            fh.write("\n")
            fh.write(code.strip() + "\n")

        return job_file

    # -----------------------------
    # Submission
    # -----------------------------
    def _submit(self, job_file: Path) -> str:
        """
        Submit job via sbatch.

        Returns:
            Job ID string.
        """
        result = subprocess.run(
            ["sbatch", str(job_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def submit(
        self,
        options: Dict[str, str],
        code: str,
        preset: Optional[str] = None,
        check_output_dir: bool = True,
        cleanup: bool = False,
    ) -> str:
        """
        Create and submit a job.

        Returns:
            Job ID.
        """
        if "output" in options and check_output_dir:
            out_dir = Path(options["output"]).parent
            if out_dir and not out_dir.exists():
                raise FileNotFoundError(f"Output directory does not exist: {out_dir}")

        job_file = self._create_script(options, code, preset)
        job_id = self._submit(job_file)

        if cleanup:
            shutil.rmtree(self.job_dir, ignore_errors=True)

        return job_id

    # -----------------------------
    # Monitoring
    # -----------------------------
    def list_jobs(self) -> List[Dict[str, str]]:
        """
        List current user's running/pending jobs.
        """
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
        