# Copyright (c) 2016 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

from kuryr_kubernetes import clients

LOG = logging.getLogger(__name__)


class Watcher(object):
    """Observes K8s resources' events using K8s '?watch=true' API.

    The `Watcher` maintains a list of K8s resources and manages the event
    processing loops for those resources. Event handling is delegated to the
    `callable` object passed as the `handler` initialization parameter that
    will be run for each K8s event observed by the `Watcher`.

    The `Watcher` can operate in two different modes based on the
    `thread_group` initialization parameter:

      - synchronous, when the event processing loops run on the same thread
        that called 'add' or 'start' methods

      - asynchronous, when each event processing loop runs on its own thread
        (`oslo_service.threadgroup.Thread`) from the `thread_group`

    When started, the `Watcher` will run the event processing loops for each
    of the K8s resources on the list. Adding a K8s resource to the running
    `Watcher` also ensures that the event processing loop for that resource is
    running.

    Stopping the `Watcher` or removing the specific K8s resource from the
    list will request the corresponding running event processing loops to
    stop gracefully, but will not interrupt any running `handler`. Forcibly
    stopping any 'stuck' `handler` is not supported by the `Watcher` and
    should be handled externally (e.g. by using `thread_group.stop(
    graceful=False)` for asynchronous `Watcher`).
    """

    def __init__(self, handler, thread_group=None):
        """Initializes a new Watcher instance.

        :param handler: a `callable` object to be invoked for each observed
                        K8s event with the event body as a single argument.
                        Calling `handler` should never raise any exceptions
                        other than `eventlet.greenlet.GreenletExit` caused by
                        `eventlet.greenthread.GreenThread.kill` when the
                        `Watcher` is operating in asynchronous mode.
        :param thread_group: an `oslo_service.threadgroup.ThreadGroup`
                             object used to run the event processing loops
                             asynchronously. If `thread_group` is not
                             specified, the `Watcher` will operate in a
                             synchronous mode.
        """
        self._client = clients.get_kubernetes_client()
        self._handler = handler
        self._thread_group = thread_group
        self._running = False

        self._resources = set()
        self._watching = {}
        self._idle = {}

    def add(self, path):
        """Adds ths K8s resource to the Watcher.

        Adding a resource to a running `Watcher` also ensures that the event
        processing loop for that resource is running. This method could block
        for `Watcher`s operating in synchronous mode.

        :param path: K8s resource URL path
        """
        self._resources.add(path)
        if self._running and path not in self._watching:
            self._start_watch(path)

    def remove(self, path):
        """Removes the K8s resource from the Watcher.

        Also requests the corresponding event processing loop to stop if it
        is running.

        :param path: K8s resource URL path
        """
        self._resources.discard(path)
        if path in self._watching:
            self._stop_watch(path)

    def start(self):
        """Starts the Watcher.

        Also ensures that the event processing loops are running. This method
        could block for `Watcher`s operating in synchronous mode.
        """
        self._running = True
        for path in self._resources - set(self._watching):
            self._start_watch(path)

    def stop(self):
        """Stops the Watcher.

        Also requests all running event processing loops to stop.
        """
        self._running = False
        for path in list(self._watching):
            self._stop_watch(path)

    def _start_watch(self, path):
        tg = self._thread_group
        self._idle[path] = True
        if tg:
            self._watching[path] = tg.add_thread(self._watch, path)
        else:
            self._watching[path] = None
            self._watch(path)

    def _stop_watch(self, path):
        if self._idle.get(path):
            if self._thread_group:
                self._watching[path].kill()

    def _watch(self, path):
        try:
            LOG.info("Started watching '%s'", path)
            for event in self._client.watch(path):
                self._idle[path] = False
                self._handler(event)
                self._idle[path] = True
                if not (self._running and path in self._resources):
                    return
        finally:
            self._watching.pop(path)
            self._idle.pop(path)
            LOG.info("Stopped watching '%s'", path)
