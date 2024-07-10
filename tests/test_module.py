"""Tests the basic functionality of the Module."""

import time
import unittest
from pathlib import Path

import requests
from wei import ExperimentClient
from wei.types import ModuleAbout, Workcell, WorkflowStatus


class TestWEI_Base(unittest.TestCase):
    """Base class for WEI's pytest tests"""

    def __init__(self, *args, **kwargs):
        """Basic setup for WEI's pytest tests"""
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).resolve().parent.parent
        self.workcell_file = self.root_dir / Path(
            "tests/workcell_defs/test_workcell.yaml"
        )
        self.workcell = Workcell.from_yaml(self.workcell_file)
        self.server_host = self.workcell.config.server_host
        self.server_port = self.workcell.config.server_port
        self.experiment = ExperimentClient(
            self.server_host,
            self.server_port,
            "TestExperiment",
        )
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.module_url = "http://camera_module:2000"
        self.redis_host = self.workcell.config.redis_host

        # Check to see that server is up
        start_time = time.time()
        while True:
            try:
                if requests.get(self.url + "/wc/state").ok:
                    break
            except Exception:
                pass
            time.sleep(1)
            if time.time() - start_time > 60:
                raise TimeoutError("Server did not start in 60 seconds")
        while True:
            try:
                if requests.get(self.module_url + "/state").ok:
                    break
            except Exception:
                pass
            time.sleep(1)
            if time.time() - start_time > 60:
                raise TimeoutError("Module did not start in 60 seconds")


class TestModuleInterfaces(TestWEI_Base):
    """Tests the basic functionality of the Module."""

    def test_take_picture_action(self):
        """Tests that the take_picture action works"""
        result = self.experiment.start_run(
            Path(self.root_dir) / Path("tests/workflow_defs/test_workflow.yaml"),
            simulate=False,
            blocking=True,
        )
        assert result["status"] == WorkflowStatus.COMPLETED
        output_path = Path("~/.wei/temp/test_image.jpg").expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.experiment.get_wf_result_file(
            run_id=result["run_id"],
            filename=result["hist"]["Take Picture"]["action_msg"],
            output_filepath=output_path,
        )
        assert Path("~/.wei/temp/test_image.jpg").expanduser().exists()

    def test_module_about(self):
        """Tests that the module's /about endpoint works"""
        response = requests.get(self.module_url + "/about")
        assert response.status_code == 200
        ModuleAbout(**response.json())


if __name__ == "__main__":
    unittest.main()
