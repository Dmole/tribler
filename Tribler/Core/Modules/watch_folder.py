import logging
import os
from twisted.internet.task import LoopingCall

from Tribler.Core.Libtorrent.LibtorrentMgr import LibtorrentMgr
from Tribler.Core.DownloadConfig import DefaultDownloadStartupConfig
from Tribler.Core.TorrentDef import TorrentDef
from Tribler.Core.Utilities.utilities import fix_torrent
from Tribler.Core.simpledefs import NTFY_WATCH_FOLDER_CORRUPT_TORRENT, NTFY_INSERT
from Tribler.pyipv8.ipv8.taskmanager import TaskManager

WATCH_FOLDER_CHECK_INTERVAL = 10


class WatchFolder(TaskManager):

    def __init__(self, session):
        super(WatchFolder, self).__init__()

        self._logger = logging.getLogger(self.__class__.__name__)
        self.session = session

    def start(self):
        self.register_task("check watch folder", LoopingCall(self.check_watch_folder))\
            .start(WATCH_FOLDER_CHECK_INTERVAL, now=False)

    def stop(self):
        self.shutdown_task_manager()

    def cleanup_torrent_file(self, root, name):
        if not os.path.exists(os.path.join(root, name)):
            self._logger.warning("File with path %s does not exist (anymore)", os.path.join(root, name))
            return

        os.rename(os.path.join(root, name), os.path.join(root, name + ".corrupt"))
        self._logger.warning("Watch folder - corrupt torrent file %s", name)
        self.session.notifier.notify(NTFY_WATCH_FOLDER_CORRUPT_TORRENT, NTFY_INSERT, None, name)

    def check_watch_folder(self):
        if not os.path.isdir(self.session.config.get_watch_folder_path()):
            return

        for root, _, files in os.walk(self.session.config.get_watch_folder_path()):
            for name in files:
                path = os.path.join(root, name)
                if  name.endswith(u".torrent"):
                    LibtorrentMgr.start_download_from_uri("file://" + path)
                if name.endswith(u".magnet"):
                    with open(path, 'r') as f:
                        magnet = f.read()
                    LibtorrentMgr.start_download_from_uri(magnet)
                    
               
