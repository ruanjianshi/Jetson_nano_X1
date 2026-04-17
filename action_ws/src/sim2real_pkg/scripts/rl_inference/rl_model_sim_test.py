#!/usr/bin/env python3

import os
import sys
import numpy as np
import time
import argparse
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/devel/lib/python3.8/site-packages')

import onnxruntime as ort


class RLModelSimulator:
    def __init__(self, model_path: str, use_gpu: bool = False):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path

        providers = ['CPUExecutionProvider']
        if use_gpu:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

        self.session = ort.InferenceSession(model_path, providers=providers)

        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

        self.input_shape = self.session.get_inputs()[0].shape
        self.output_shape = self.session.get_outputs()[0].shape

        print(f"=" * 50)
        print(f"  RL Model Simulator")
        print(f"=" * 50)
        print(f"  Model: {model_path}")
        print(f"  Input: {self.input_names} {self.input_shape}")
        print(f"  Output: {self.output_names} {self.output_shape}")
        print(f"  Providers: {providers}")
        print(f"=" * 50)

    def infer(self, obs: np.ndarray) -> np.ndarray:
        if obs.ndim == 1:
            obs = obs.reshape(1, -1)

        outputs = self.session.run(self.output_names, {self.input_names[0]: obs.astype(np.float32)})
        return outputs[0]

    def random_obs(self) -> np.ndarray:
        return np.random.randn(1, self.input_shape[1]).astype(np.float32)

    def zero_obs(self) -> np.ndarray:
        return np.zeros((1, self.input_shape[1]), dtype=np.float32)


class JumpModelSimulator:
    def __init__(self, model_path: str):
        self.model = RLModelSimulator(model_path)

    def test_random(self, num_tests: int = 10) -> List[Dict]:
        results = []

        print(f"\n{'='*50}")
        print(f"  Test 1: Random Observations ({num_tests} iterations)")
        print(f"{'='*50}")

        total_time = 0
        for i in range(num_tests):
            obs = self.model.random_obs()

            start = time.time()
            action = self.model.infer(obs)
            inference_time = (time.time() - start) * 1000
            total_time += inference_time

            results.append({
                'iteration': i + 1,
                'obs_mean': float(np.mean(obs)),
                'action': action[0].tolist(),
                'inference_time_ms': inference_time
            })

            if (i + 1) % 5 == 0 or i == 0:
                print(f"  [{i+1:3d}] obs_mean={np.mean(obs):7.3f} | "
                      f"action=[{action[0][0]:6.2f}, {action[0][1]:6.2f}, {action[0][2]:6.2f}, "
                      f"{action[0][3]:6.2f}, {action[0][4]:6.2f}, {action[0][5]:6.2f}] | "
                      f"{inference_time:6.2f}ms")

        avg_time = total_time / num_tests
        print(f"\n  Average inference time: {avg_time:.2f}ms")
        print(f"  Estimated FPS: {1000/avg_time:.1f}")

        return results

    def test_latency(self, num_tests: int = 100) -> Dict:
        print(f"\n{'='*50}")
        print(f"  Test 2: Latency Test ({num_tests} iterations)")
        print(f"{'='*50}")

        warmup = 5
        for i in range(warmup):
            obs = self.model.random_obs()
            _ = self.model.infer(obs)

        latencies = []
        for i in range(num_tests):
            obs = self.model.random_obs()

            start = time.time()
            action = self.model.infer(obs)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        latencies = np.array(latencies)

        print(f"  Warmup: {warmup} iterations")
        print(f"  Samples: {num_tests} iterations")
        print(f"")
        print(f"  Latency Statistics:")
        print(f"    Min:    {np.min(latencies):.2f}ms")
        print(f"    Max:    {np.max(latencies):.2f}ms")
        print(f"    Mean:   {np.mean(latencies):.2f}ms")
        print(f"    Median: {np.median(latencies):.2f}ms")
        print(f"    Std:    {np.std(latencies):.2f}ms")
        print(f"    P95:    {np.percentile(latencies, 95):.2f}ms")
        print(f"    P99:    {np.percentile(latencies, 99):.2f}ms")
        print(f"")
        print(f"  Throughput:")
        print(f"    Mean FPS:   {1000/np.mean(latencies):.1f}")
        print(f"    Min FPS:    {1000/np.max(latencies):.1f}")
        print(f"    Max FPS:    {1000/np.min(latencies):.1f}")

        return {
            'min_ms': float(np.min(latencies)),
            'max_ms': float(np.max(latencies)),
            'mean_ms': float(np.mean(latencies)),
            'median_ms': float(np.median(latencies)),
            'std_ms': float(np.std(latencies)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99)),
            'mean_fps': float(1000/np.mean(latencies))
        }

    def test_continues(self, num_iterations: int = 50, interval_ms: float = 20.0) -> Dict:
        print(f"\n{'='*50}")
        print(f"  Test 3: Continuous Inference")
        print(f"  Iterations: {num_iterations}, Interval: {interval_ms}ms")
        print(f"{'='*50}")

        interval_sec = interval_ms / 1000.0
        latencies = []
        real_intervals = []

        obs = self.model.zero_obs()

        print(f"\n  Starting continuous inference...")

        start_total = time.time()
        for i in range(num_iterations):
            iter_start = time.time()

            action = self.model.infer(obs)
            latency = (time.time() - iter_start) * 1000
            latencies.append(latency)

            if i < 10 or i >= num_iterations - 3:
                print(f"  [{i+1:3d}] action=[{action[0][0]:6.2f}, {action[0][1]:6.2f}, "
                      f"{action[0][2]:6.2f}, {action[0][3]:6.2f}, {action[0][4]:6.2f}, "
                      f"{action[0][5]:6.2f}] | {latency:5.2f}ms")

            real_interval = time.time() - iter_start
            real_intervals.append(real_interval * 1000)

            target_time = start_total + (i + 1) * interval_sec
            sleep_time = target_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        total_time = time.time() - start_total

        latencies = np.array(latencies)
        real_intervals = np.array(real_intervals)

        print(f"\n  Summary:")
        print(f"    Total time: {total_time:.2f}s (target: {num_iterations * interval_sec:.2f}s)")
        print(f"    Expected interval: {interval_ms}ms")
        print(f"    Real interval: {np.mean(real_intervals):.2f}ms (std: {np.std(real_intervals):.2f}ms)")
        print(f"    Achieved FPS: {num_iterations / total_time:.1f}")

        return {
            'total_time': total_time,
            'mean_latency_ms': float(np.mean(latencies)),
            'mean_interval_ms': float(np.mean(real_intervals)),
            'achieved_fps': float(num_iterations / total_time)
        }


def main():
    parser = argparse.ArgumentParser(description='RL Model Simulation Test')
    parser.add_argument('--model', type=str,
                        default='/home/jetson/Desktop/Jetson_Nano/action_ws/src/sim2real_pkg/models/jump_model.onnx',
                        help='Path to ONNX model')
    parser.add_argument('--test', type=str, default='all',
                        choices=['all', 'random', 'latency', 'continuous'],
                        help='Test type')
    parser.add_argument('--iterations', type=int, default=100,
                        help='Number of iterations')
    parser.add_argument('--interval', type=float, default=20.0,
                        help='Interval in ms for continuous test')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  RL Model Simulation Test")
    print("=" * 60)
    print(f"  Model: {args.model}")
    print(f"  Test: {args.test}")
    print("=" * 60)

    try:
        simulator = JumpModelSimulator(args.model)

        if args.test == 'all':
            simulator.test_random(num_tests=min(args.iterations, 20))
            simulator.test_latency(num_tests=args.iterations)
            simulator.test_continues(num_iterations=min(args.iterations, 50),
                                   interval_ms=args.interval)

        elif args.test == 'random':
            simulator.test_random(num_tests=args.iterations)

        elif args.test == 'latency':
            simulator.test_latency(num_tests=args.iterations)

        elif args.test == 'continuous':
            simulator.test_continues(num_iterations=args.iterations,
                                   interval_ms=args.interval)

        print("\n" + "=" * 60)
        print("  All tests completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
