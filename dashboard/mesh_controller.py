from consts import ConnStatuses


class MeshController:
    MAX_WAIT_TIME: int = 60

    _has_been_updated: bool
    _network_name: str
    _mesh_name: str
    _time_since_last_message: int
    _conn_status: ConnStatuses

    def __init__(self):
        self._conn_status = ConnStatuses.DISCONNECTED
        self._network_name = ''
        self._mesh_name = ''
        self._time_since_last_message = self.MAX_WAIT_TIME - 1
        self._has_been_updated = False

    def update_status(self, mesh_name: str, network_name: str):
        self._mesh_name = mesh_name
        self._network_name = network_name
        self._conn_status = ConnStatuses.CONNECTED
        self._has_been_updated = True

    def get_status(self):
        return self._mesh_name, self._network_name, self._conn_status
    
    def reset_time_since_last_msg(self):
        self._time_since_last_message = 0

    @property
    def has_been_updated(self):
        return self._has_been_updated
    
    @property
    def check_conn(self):
        if self._time_since_last_message > self.MAX_WAIT_TIME:
            self._time_since_last_message = 0
            self._conn_status = ConnStatuses.DISCONNECTED
            return True
        self._time_since_last_message += 1
        return False
        
