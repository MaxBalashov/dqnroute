from functools import total_ordering
from copy import deepcopy
# import pandas as pd
# import numpy as np

class Message:
    """
    Base class for all messages used in the system
    """

    def __init__(self, **kwargs):
        self.contents = kwargs

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, str(self.contents))

    def __repr__(self):
        return '<{}>'.format(str(self))

    def __getattr__(self, name):
        try:
            return super().__getattribute__('contents')[name]
        except KeyError:
            raise AttributeError(name)

    def getContents(self):
        return self.contents

class UnsupportedMessageType(Exception):
    """
    Exception which is thrown by message handlers on encounter of
    unknown message type
    """
    pass

class InitMessage(Message):
    """
    Message which router receives as environment starts
    """
    def __init__(self, config):
        super().__init__(config=config)

class _TransferMessage(Message):
    """
    Wrapper message which is used to send data between nodes
    """
    def __init__(self, from_node: int, to_node: int, inner_msg: Message):
        super().__init__(from_node=from_node, to_node=to_node, inner_msg=inner_msg)

class InMessage(_TransferMessage):
    """
    Wrapper message which has came from the outside.
    """
    pass

class OutMessage(_TransferMessage):
    """
    Wrapper message which is sent to a neighbor through the interface
    with given ID.
    """
    pass

class SectionMessage(Message):
    """
    Wrapper message which targets a particular subhandler
    """
    def __init__(self, section: int, inner_msg: Message):
        super().__init__(section=section, inner_msg=inner_msg)

class ServiceMessage(Message):
    """
    Message which does not contain a package and, hence,
    contains no destination.
    """
    pass

# Packages
@total_ordering
class Package:
    def __init__(self, pkg_id, size, dst, start_time, contents):
        self.id = pkg_id
        self.size = size
        self.dst = dst
        self.start_time = start_time
        self.contents = contents
        # self.route = None
        # self.rnn_state = (np.zeros((1, state_size)),
        #                   np.zeros((1, state_size)))

    # def route_add(self, data, cols):
    #     if self.route is None:
    #         self.route = pd.DataFrame(columns=cols)
    #     self.route.loc[len(self.route)] = data

    def __str__(self):
        return '{}#{}{}'.format(self.__class__.__name__, self.id,
                                str((self.dst, self.size, self.start_time, self.contents)))

    def __hash__(self):
        return hash((self.id, self.contents))

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

class Bag(Package):
    def __init__(self, bag_id, dst, start_time, contents):
        super().__init__(bag_id, 0, dst, start_time, contents)
        self.energy_overhead = 0

    def spend_energy(self, x: int):
        self.energy_overhead += x

class PkgMessage(Message):
    """
    Message which contains a package which has a particular
    destination.
    """
    def __init__(self, pkg: Package):
        super().__init__(pkg=pkg)

class PkgReceivedMessage(Message):
    """
    Message which router uses in case it was the package's
    destination
    """
    def __init__(self, pkg: Package):
        super().__init__(pkg=pkg)

class LinkUpdateMessage(Message):
    """
    Message which router receives when graph topology is changed
    """
    def __init__(self, to: int, direction='both', **kwargs):
        super().__init__(to=to, direction=direction, **kwargs)

class AddLinkMessage(LinkUpdateMessage):
    """
    Message which router receives when a link is connected (or restored).
    """
    def __init__(self, to: int, direction='both', params={}):
        super().__init__(to, direction, params=params)

class RemoveLinkMessage(LinkUpdateMessage):
    """
    Message which router receives when link breakage is detected
    """
    def __init__(self, to: int, direction='both'):
        super().__init__(to, direction)

#
# Service messages
#

class RewardMsg(ServiceMessage):
    def __init__(self, pkg_id: int, Q_estimate: float, reward_data):
        super().__init__(pkg_id=pkg_id, Q_estimate=Q_estimate, reward_data=reward_data)

class NetworkRewardMsg(RewardMsg):
    def __init__(self, pkg_id: int, Q_estimate: float, time_received: float):
        super().__init__(pkg_id, Q_estimate, time_received)

class ConveyorRewardMsg(RewardMsg):
    def __init__(self, bag_id: int, Q_estimate: float, time_processed: float,
                 energy_gap: float):
        super().__init__(bag_id, Q_estimate, (time_processed, energy_gap))

class StateAnnouncementMsg(ServiceMessage):
    def __init__(self, node: int, seq: int, state):
        super().__init__(node=node, seq=seq, state=state)
