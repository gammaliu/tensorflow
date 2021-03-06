# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests and benchmarks for interacting with the `tf.Session`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time

import numpy as np
import tensorflow as tf


class SessionBenchmark(tf.test.Benchmark):
  """Tests and benchmarks for interacting with the `tf.Session`."""

  def _benchmarkFeed(self, name, target, size, iters):
    """Runs a microbenchmark to measure the cost of feeding a tensor.

    Reports the median cost of feeding a tensor of `size` * `sizeof(float)`
    bytes.

    Args:
      name: A human-readable name for logging the output.
      target: The session target to use for the benchmark.
      size: The number of floating-point numbers to be feed.
      iters: The number of iterations to perform.
    """
    feed_val = np.random.rand(size).astype(np.float32)
    times = []
    with tf.Graph().as_default():
      p = tf.placeholder(tf.float32, shape=[size])
      # Fetch the operation rather than the tensor, to avoid measuring the time
      # to fetch back the value.
      no_op = tf.identity(p).op
      with tf.Session(target) as sess:
        sess.run(no_op, feed_dict={p: feed_val})  # Warm-up run.
        for _ in xrange(iters):
          start_time = time.time()
          sess.run(no_op, feed_dict={p: feed_val})
          end_time = time.time()
          times.append(end_time - start_time)
    print("%s %d %f" % (name, size, np.median(times)))
    self.report_benchmark(iters=iters, wall_time=np.median(times),
                          name=name)

  def _benchmarkFetch(self, name, target, size, iters):
    """Runs a microbenchmark to measure the cost of fetching a tensor.

    Reports the median cost of fetching a tensor of `size` * `sizeof(float)`
    bytes.

    Args:
      name: A human-readable name for logging the output.
      target: The session target to use for the benchmark.
      size: The number of floating-point numbers to be fetched.
      iters: The number of iterations to perform.
    """
    times = []
    with tf.Graph().as_default():
      # Define the tensor to be fetched as a variable, to avoid
      # constant-folding.
      v = tf.Variable(tf.random_normal([size]))
      with tf.Session(target) as sess:
        sess.run(v.initializer)
        sess.run(v)  # Warm-up run.
        for _ in xrange(iters):
          start_time = time.time()
          sess.run(v)
          end_time = time.time()
          times.append(end_time - start_time)
    print("%s %d %f" % (name, size, np.median(times)))
    self.report_benchmark(iters=iters, wall_time=np.median(times),
                          name=name)

  def benchmarkGrpcSession(self):
    server = tf.train.Server.create_local_server()
    self._benchmarkFeed("benchmark_session_feed_grpc_4B",
                        server.target, 1, 10000)
    tf.Session.reset(server.target)
    self._benchmarkFeed("benchmark_session_feed_grpc_4MB",
                        server.target, 1 << 20, 100)
    tf.Session.reset(server.target)
    self._benchmarkFetch("benchmark_session_fetch_grpc_4B",
                         server.target, 1, 20000)
    tf.Session.reset(server.target)
    self._benchmarkFetch("benchmark_session_fetch_grpc_4MB",
                         server.target, 1 << 20, 100)
    tf.Session.reset(server.target)

  def benchmarkDirectSession(self):
    self._benchmarkFeed("benchmark_session_feed_direct_4B",
                        "", 1, 5000)
    self._benchmarkFeed("benchmark_session_feed_direct_4MB",
                        "", 1 << 20, 200)
    self._benchmarkFetch("benchmark_session_fetch_direct_4B",
                         "", 1, 5000)
    self._benchmarkFetch("benchmark_session_fetch_direct_4MB",
                         "", 1 << 20, 100)


if __name__ == "__main__":
  tf.test.main()
