'''Defines basic SDK constants and classes.

All public names here are also re-exported from :mod:`oneagent.sdk` and should
preferably be used from there.
'''

import os

_DEBUG_LEAKS = False

if _DEBUG_LEAKS:
    import traceback

class _Uninstantiable(object):
    '''Classes deriving from this class cannot be instantiated.'''

    def __new__(cls):
        raise ValueError('Attempt to instantiate')

class AgentState(_Uninstantiable):
    '''Constants for the agent's state. See
    :attr:`oneagent.sdk.SDK.agent_state`.'''

    #: The SDK stub is connected to the agent, which is currently active.
    ACTIVE = 0

    #: The SDK stub is connected to the agent, which is temporarily inactive.
    TEMPORARILY_INACTIVE = 1

    #: The SDK stub is connected to the agent, which is permanently inactive.
    PERMANENTLY_INACTIVE = 2


    #: The agent has not been initialized.
    NOT_INITIALIZED = 3

    #: Some unexpected error occurred while trying to determine the agent state.
    ERROR = -1

class ErrorCode(_Uninstantiable):
    '''Constants for error codes of the native agent, as may be contained in
    :attr:`.SDKError.code`.'''

    # Same bit pattern if interpreted in 32 bit unsigned / two's complement
    _ERROR_BASE = 0xAFFE0000 if os.name == 'nt' else -0x50020000

    #: The operation completed successfully. You usually won't get any object
    #: with error code at all in that case.
    SUCCESS = 0

    #: The operation failed, but no more specific error code fits the failure.
    GENERIC = _ERROR_BASE + 1

    #: A function was called with an invalid argument.
    INVALID_ARGUMENT = _ERROR_BASE + 2

    NOT_IMPLEMENTED = _ERROR_BASE + 3 #: The called function is not implemented.

    NOT_INITIALIZED = _ERROR_BASE + 4 #: The SDK has not been initialized.

    #: There is not enough available memory to complete the operation.
    OUT_OF_MEMORY = _ERROR_BASE + 5

    #: The native SDK stub was configured to _not_ try to load the actual agent
    #: module.
    AGENT_NOT_ACTIVE = _ERROR_BASE + 6

    #: The loader module was unable to load the actual native SDK agent module.
    LOAD_AGENT = _ERROR_BASE + 7

    #: The loader module found an SDK agent binary, but it didn't have the
    #: expected exports.
    INVALID_AGENT_BINARY = _ERROR_BASE + 8

    #: The operation failed because of an unexpected error.
    UNEXPECTED = _ERROR_BASE + 9

    #: The command line argument / stub variable definition was ignored because
    #: an entry with the same key was already present.
    ENTRY_ALREADY_EXISTS = _ERROR_BASE + 10

    #: The SDK agent module doesn't support the feature level required by this
    #: version of the SDK stub.
    FEATURE_LEVEL_NOT_SUPPORTED = _ERROR_BASE + 11

    #: The SDK agent module doesn't support the SDK interface required by this
    #: version of the SDK stub
    INTERFACE_NOT_SUPPORTED = _ERROR_BASE + 12

    #: The operation failed because this is the child process of a fork that
    #: occurred while the SDK was initialized.
    FORK_CHILD = _ERROR_BASE + 13

class MessageSeverity(_Uninstantiable): # Private
    '''Constants for the severity of log messages.

    The levels with the lower numerical values include all messages of the ones
    with the higher values. Note that :attr:`.DEBUG` is the highest severity,
    contrary to usual conventions.'''

    FINEST = 0 #: Most verbose logging (higly detailed tracing).
    FINER = 1 #: Slightly less verbose logging (fairly detailed tracing).
    FINE = 2 #: Still verbose logging (informational tracing messages).
    CONFIG = 3 #: Log configuration messages.
    INFO = 4 #: Log informational messages.
    WARNING = 5 #: Log conditions that indicate a potential problem.
    SEVERE = 6 #: Log messages indicating a serious failure.

    #: Debug message. None should be logged by default, unless they are
    #: specifically enabled with special debug options. Note that contrary to
    #: usual conventions, this is the highest severity.
    DEBUG = 7

    #: No messages of this level exist, so using this level disables all log
    #: messages.
    NONE = 8

class DatabaseVendor(_Uninstantiable):
    '''String constants for well-known database vendors. Use for the
    :code:`vendor` parameter of
    :meth:`oneagent.sdk.SDK.create_database_info`.'''

    APACHE_HIVE = "ApacheHive" #: Database vendor string for Apache Hive.

    #: Database vendor string for Apache Derby (aka. IBM Cloudscape).
    CLOUDSCAPE = "Cloudscape"

    HSQLDB = "HSQLDB" #: Database vendor string for HyperSQL DB.

    #: Database vendor string for OpenEdge Database (aka. Progress).
    PROGRESS = "Progress"

    MAXDB = "MaxDB" #: Database vendor string for SAP MaxDB.
    HANADB = "HanaDB" #: Database vendor string for SAP HANA DB.
    INGRES = "Ingres" #: Database vendor string for Ingres Database.
    FIRST_SQL = "FirstSQL" #: Database vendor string for FirstSQL.
    ENTERPRISE_DB = "EnterpriseDB" #: Database vendor string for EnterpriseDB.
    CACHE = "Cache" #: Database vendor string for InterSystems Cache.
    ADABAS = "Adabas" #: Database vendor string for ADABAS.
    FIREBIRD = "Firebird" #: Database vendor string for Firebird Database.
    DB2 = "DB2" #: Database vendor string for IBM Db2.

    #: Database vendor string for JDBC connections to Apache Derby
    #: (aka. IBM Cloudscape).
    DERBY_CLIENT = "Derby Client"

    #: Database vendor string for Derby Embedded.
    DERBY_EMBEDDED = "Derby Embedded"

    FILEMAKER = "Filemaker" #: Database vendor string for FileMaker Pro.
    INFORMIX = "Informix" #: Database vendor string for IBM Informix.
    INSTANT_DB = "InstantDb" #: Database vendor string for InstantDB.
    INTERBASE = "Interbase" #: Database vendor string for Embarcadero InterBase.
    MYSQL = "MySQL" #: Database vendor string for MySQL.
    MARIADB = "MariaDB" #: Database vendor string for MariaDB.
    NETEZZA = "Netezza" #: Database vendor string for IBM Netezza.
    ORACLE = "Oracle" #: Database vendor string for Oracle Database.
    PERVASIVE = "Pervasive" #: Database vendor string for Pervasive PSQL.
    POINTBASE = "Pointbase" #: Database vendor string for PointBase.
    POSTGRESQL = "PostgreSQL" #: Database vendor string for PostgreSQL.
    SQLSERVER = "SQL Server" #: Database vendor string for Microsoft SQL Server.
    SQLITE = "sqlite" #: Database vendor string for SQLite.

    #: Database vendor string for SAP ASE
    #: (aka. Sybase SQL Server, Sybase DB, Sybase ASE).
    SYBASE = "Sybase"

    TERADATA = "Teradata" #: Database vendor string for Teradata Database.
    VERTICA = "Vertica" #: Database vendor string for Vertica.
    CASSANDRA = "Cassandra" #: Database vendor string for Cassandra.
    H2 = "H2" #: Database vendor string for H2 Database Engine.

    #: Database vendor string for ColdFusion In-Memory Query
    #: (aka. Query of Queries).
    COLDFUSION_IMQ = "ColdFusion IMQ"

    REDSHIFT = "Amazon Redshift" #: Database vendor string for Amazon Redshift.

class ChannelType(_Uninstantiable):
    '''Constants for communication channel types, for use as
    :attr:`oneagent.sdk.Channel.type_`'''
    OTHER = 0 #: Some other channel type or unknown channel type.

    #: The channel is a TCP/IP connection.
    #:
    #: The channel endpoint string should be the host name, followed by a colon,
    #: followed by the port number (in decimal).  E.g. :code:`localhost:1234` or
    #: :code:`example.com:80`.
    TCP_IP = 1

    #: The channel is a connection via Unix domain sockets.
    #:
    #: The channel endpoint string should be the path of the Unix domain
    #: sockets.
    UNIX_DOMAIN_SOCKET = 2

    #: The channel is a named pipe.
    #:
    #: The channel endpoint string should be the pipe name.
    NAMED_PIPE = 3

    #: The channel is some in-process means of communication.
    IN_PROCESS = 4

class SDKError(Exception):
    '''Exception for SDK errors (mostly during initialization, see
    :func:`oneagent.try_init`).'''
    def __init__(self, code, msg):
        super(SDKError, self).__init__(code, msg)

        #: An :class:`int` error code. Can be one of the :class:`.ErrorCode`
        #: constants. If not, it is a Windows error code on Windows and an errno
        #: number on other systems.
        self.code = code

        #: The :class:`str` error message associated with :attr:`code`
        #: (potentially contains more information than could be deduced from
        #: :attr:`code` alone).
        self.message = msg

class SDKHandleBase(object):
    '''Base class for SDK handles that must be closed explicitly.

    You can use this class as a context manager (i.e. with a :code:`with`-block)
    to automatically close the handle.'''

    def __init__(self, nsdk, handle):
        self.handle = handle
        self.nsdk = nsdk
        if _DEBUG_LEAKS:
            self.alloc_at = ''.join(traceback.format_stack())

    def close_handle(self, nsdk, handle):
        raise NotImplementedError(
            'Must implement close_handle in derived class')

    def __del__(self):
        if self.handle is None:
            return
        try:
            warn = self.nsdk.agent_get_logging_callback()
            if not warn:
                return
            if _DEBUG_LEAKS:
                warn(
                    'Unclosed SDK handle '
                    + repr(self)
                    + b' from '
                    + self.alloc_at)
            else:
                warn('Unclosed SDK handle ' + repr(self))

        finally:
            self.close()

    def __str__(self):
        return '{}({})'.format(type(self), self.handle)

    def close(self):
        '''Closes the handle, if it is still open.

        Usually, you should prefer using the handle as a context manager to
        calling :meth:`close` manually.'''
        if self.handle is not None:
            self.close_handle(self.nsdk, self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def __bool__(self):
        return bool(self.handle)

    __nonzero__ = __bool__

class DbInfoHandle(SDKHandleBase):
    '''Opaque handle to database information. See
        :meth:`oneagent.sdk.SDK.create_database_info`.'''
    def close_handle(self, nsdk, handle):
        nsdk.databaseinfo_delete(handle)

class WebapplicationInfoHandle(SDKHandleBase):
    '''Opaque handle to web application information. See
        :meth:`oneagent.sdk.SDK.create_web_application_info`.'''
    def close_handle(self, nsdk, handle):
        nsdk.webapplicationinfo_delete(handle)
