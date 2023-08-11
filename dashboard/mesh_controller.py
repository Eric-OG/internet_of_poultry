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

    def refresh_connection_status(self):
        self._conn_status = ConnStatuses.CONNECTED
        self._time_since_last_message = 0

    def update_mesh_status(self, mesh_name: str, network_name: str):
        self._mesh_name = mesh_name
        self._network_name = network_name
        self._has_been_updated = True

    def get_mesh_status(self):
        return self._mesh_name, self._network_name, self._conn_status

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
        
