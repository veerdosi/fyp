"""Matched, sensor-only computation permissions for episode policy prompts."""
from pathlib import Path


def computation_access(run):
    run = Path(run).resolve()
    root = Path(__file__).resolve().parents[2]
    return (
        'Updated in-episode computation permission: this supersedes the earlier no-code restriction. '
        'You may write and execute temporary Python code for calculations from your policy-visible '
        'RGB images, metric depth arrays, camera calibration and robot measurements, then use those '
        'results to choose sensing queries, direct poses or waypoints. You own these calculations '
        'and robot decisions. Sol owns experiment code and the repository. '
        f'Read only this episode\'s public sensor files under {run}/public and your own calculation '
        f'artifacts. Write code and generated files only under {run}/policy_compute. '
        'Use functions exec with tools.exec_command to write your Python source there; execute '
        'every calculation through the following logging wrapper, which captures code, stdout, '
        'stderr, status, available input manifest and timing: '
        f'{root}/.venv/bin/python {root}/scripts/policy/policy_calc.py --run {run} '
        f'--code {run}/policy_compute/YOUR_SCRIPT.py. '
        'Each execution has a 30-second limit. Available libraries include numpy, scipy, cv2 and '
        'Pillow. Environment variables POLICY_OBSERVATION_FOLDER, POLICY_PUBLIC_FOLDER and '
        'POLICY_COMPUTE_FOLDER identify your current inputs and scratch directory. '
        'You may use tools.view_image for supplied images or your own generated calculation images, '
        'and cat permitted sensor JSON or your own calculation files. Do not read other repository '
        'files or other episodes; do not import fyp, mujoco or robosuite, access the simulator '
        'process, hidden object poses, contacts, reward, scoring or external network. Do not change '
        'the experiment code or submit robot commands through code. Return robot decisions using '
        'the existing JSON command schema. Do not spawn or delegate to other agents.'
    )
