# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Package for handling a list of objects of the same type as a given one."""

import threading
from Common import orb


class PeerList(object):

    """Class that builds a list of objects of the same type as this one."""

    def __init__(self, owner):
        self.owner = owner
        self.lock = threading.Condition()
        self.peers = {}

    # Public methods

    def initialize(self):
        """Populates the list of existing peers and registers the current
        peer at each of the discovered peers.

        It only adds the peers with lower ids than this one or else
        deadlocks may occur. This method must be called after the owner
        object has been registered with the name service.

        """

        self.lock.acquire()
        try:
            peers_to_register_at = self.owner.name_service.require_all(self.owner.type)
            for peer_id, peer_address in peers_to_register_at:
                if peer_id >= self.owner.id:
                    continue
                self.peers[peer_id] = orb.Stub(peer_address)

            for peer_id, peer_address in self.peers.items():
                peer = self.peers[peer_id]
                try:
                    peer.register_peer(self.owner.id, self.owner.address)
                except Exception as e:
                    del self.peers[peer_id]
        finally:
            self.lock.release()

    def destroy(self):
        """Unregister this peer from all others in the list."""

        self.lock.acquire()
        try:
            registered_peers = self.peers
            if registered_peers:
                for peer_id, peer_address in registered_peers.items():
                    print(len(self.peers))
                    peer = self.peers[peer_id]
                    try:
                        peer.unregister_peer(self.owner.id)
                    except Exception:
                        continue
        finally:
            self.lock.release()

    def register_peer(self, pid, paddr):
        """Register a new peer joining the network."""

        # Synchronize access to the peer list as several peers might call
        # this method in parallel.
        self.lock.acquire()
        try:
            self.peers[pid] = orb.Stub(paddr)
            print("Peer {} has joined the system.".format(pid))
        finally:
            self.lock.release()

    def unregister_peer(self, pid):
        """Unregister a peer leaving the network."""
        # Synchronize access to the peer list as several peers might call
        # this method in parallel.

        self.lock.acquire()
        try:
            if pid in self.peers:
                del self.peers[pid]
                print("Peer {} has left the system.".format(pid))
            else:
                raise Exception("No peer with id: '{}'".format(pid))
        finally:
            self.lock.release()

    def display_peers(self):
        """Display all the peers in the list."""

        self.lock.acquire()
        try:
            pids = sorted(self.peers.keys())
            print("List of peers of type '{}':".format(self.owner.type))
            for pid in pids:
                addr = self.peers[pid].address
                print("    id: {:>2}, address: {}".format(pid, addr))
        finally:
            self.lock.release()

    def peer(self, pid):
        """Return the object with the given id."""

        self.lock.acquire()
        try:
            return self.peers[pid]
        finally:
            self.lock.release()

    def get_peers(self):
        """Return all registered objects."""

        self.lock.acquire()
        try:
            return self.peers
        finally:
            self.lock.release()
