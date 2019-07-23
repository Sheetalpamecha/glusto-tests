#  Copyright (C) 2017-2018  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
   Description: Library for gluster geo-replication operations
"""

from glusto.core import Glusto as g


def georep_createpem(mnode):
    """ Creates a common pem pub file on all the nodes in the master and
        is used to implement the passwordless SSH connection
    Args:
        mnode (str): Node on which cmd is to be executed
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = "gluster system:: execute gsec_create"
    return g.run(mnode, cmd)


def georep_ssh_keygen(mnode):
    """ Creates a pair of ssh private and public key if not present

    Args:
        mnode (str): Node on which cmd is to be executed
    Returns:
        bool : True if ssh-keygen is successful on all servers.
            False otherwise. It also returns True if ssh key
            is already present

    """
    cmd = 'echo -e "n" | ssh-keygen -f ~/.ssh/id_rsa -q -N ""'
    ret, out, _ = g.run(mnode, cmd)
    if ret and "already exists" not in out:
        return False
    return True


def georep_ssh_copyid(mnode, tonode, user, passwd):
    """ Copies the default ssh public key onto tonode's
        authorized_keys file

    Args:
        mnode (str): Node on which cmd is to be executed
        tonode (str): Node to which ssh key is to be copied
        user (str): user of tonode
        passwd (str): passwd of the user of tonode
    Returns:
        bool : True if ssh-copy-id is successful to tonode.
            False otherwise. It also returns True if ssh key
            is already present

    """
    cmd = ('sshpass -p "%s" ssh-copy-id -o StrictHostKeyChecking=no %s@%s' %
           (passwd, user, tonode))
    ret, _, _ = g.run(mnode, cmd)
    if ret:
        return False
    return True


def georep_groupadd(servers, groupname):
    """ Creates a group in all the slave nodes where a user will be added
        to set up a non-root session

    Args:
        servers (list): list of nodes on which cmd is to be executed
        groupname (str): Specifies a groupname

    Returns:
        bool : True if add group is successful on all servers.
            False otherwise.

    """
    cmd = "groupadd %s" % groupname
    results = g.run_parallel(servers, cmd)

    _rc = True
    for server, ret_value in list(results.items()):
        retcode, _, err = ret_value
        if retcode != 0 and "already exists" not in err:
            g.log.error("Unable to add group %s on server %s",
                        groupname, server)
            _rc = False
    if not _rc:
        return False

    return True


def georep_geoaccount(servers, groupname, groupaccount):
    """ Creates a user account with which the geo-rep session can be securely
        set up

    Args:
        servers (list): list of nodes on which cmd is to be executed
        groupname (str): Specifies a groupname
        groupaccount (str): Specifies the user account to set up geo-rep

    Returns:
        bool : True if user add is successful on all servers.
            False otherwise.

    """
    cmd = "useradd -G %s %s" % (groupname, groupaccount)
    results = g.run_parallel(servers, cmd)

    _rc = True
    for server, ret_value in list(results.items()):
        retcode, _, err = ret_value
        if retcode != 0 and "already exists" not in err:
            g.log.error("Unable to add user on %s", server)
            _rc = False
    if not _rc:
        return False

    return True


def georep_geoaccount_setpasswd(servers, groupname, groupaccount, passwd):
    """ Creates a user account with which the geo-rep session can be securely
        set up

    Args:
        servers (list): list of nodes on which cmd is to be executed
        groupname (str): Specifies a groupname
        groupaccount (str): Specifies the user account to set up geo-rep
        passwd (str): Specifies password for they groupaccount

    Returns:
        bool : True if password set is successful on all servers.
            False otherwise.

    """
    cmd = "echo %s:%s | chpasswd" % (groupaccount, passwd)
    results = g.run_parallel(servers, cmd)

    _rc = True
    for server, ret_value in list(results.items()):
        retcode, _, err = ret_value
        if retcode != 0:
            g.log.error("Unable to set passwd for user %s on %s",
                        groupaccount, server)
            _rc = False
    if not _rc:
        return False

    return True


def georep_mountbroker_setup(mnode, groupname, directory):
    """ Sets up mountbroker root directory and group

    Args:
        mnode (str): Node on which command is to be executed
        groupname (str) : Specifies the groupname used
        directory (str) : Specifies mountbroker root directory

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = "gluster-mountbroker setup %s %s" % (directory, groupname)
    return g.run(mnode, cmd)


def georep_mountbroker_adduser(mnode, slavevol, useraccount):
    """ Adds the volume and user to the mountbroker

    Args:
        mnode (str): Node on which command is to be executed
        slavevol (str) : The slave volume name
        useraccount (str): The user with which geo-rep is to be set up

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = "gluster-mountbroker add %s %s" % (slavevol, useraccount)
    return g.run(mnode, cmd)


def georep_mountbroker_status(mnode):
    """ Displays the status of every peer node in the slave cluster

    Args:
        mnode (str): Node on which command is to be executed


    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = "gluster-mountbroker status"
    return g.run(mnode, cmd)


def georep_set_pemkeys(mnode, useraccount, mastervol, slavevol):
    """ Sets geo-rep pem keys

    Args:
        mnode (str): Node on which command is to be executed
        useraccount (str) : User with which geo-rep is to be set up
        mastervol (str) : The master volume
        slavevol (str): The slave volume

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = ("/usr/libexec/glusterfs/set_geo_rep_pem_keys.sh %s %s %s" %
           (useraccount, mastervol, slavevol))
    return g.run(mnode, cmd)


def georep_status(mnode, mastervol, slaveip, slavevol, user=None):
    """Shows the status of the geo-replication session
    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol(str): The name of the slave volume
    Kwargs:
        user (str): If not set, the default is a root-user
            If specified, non-root user participates in geo-rep
            session
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.
            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.
            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        cmd = ("gluster volume geo-replication %s %s@%s::%s status" %
               (mastervol, user, slaveip, slavevol))
    else:
        cmd = ("gluster volume geo-replication %s %s::%s status" %
               (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_create(mnode, mastervol, slaveip, slavevol, user=None, force=False):
    """Pushes the keys to all the slave nodes and creates a geo-rep session
    Args:
        mnode (str) : Node on which cmd is to be executed
        mastervol (str) : The name of the mastervol
        slaveip (str): SlaveIP
        slavevol (str) The name of the slave volume
    kwargs:
        force (bool): If this option is set to True, then create geo-rep
            session will be executed with the force option.
            If it is set to False, then the geo-rep session is created
            without the force option
        user (str): If not set, the default is a root-user
            If specified, non-root user participates in the geo-rep
            session

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        if force:
            cmd = ("gluster volume geo-replication %s %s@%s::%s create "
                   "push-pem force" % (mastervol, user, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s@%s::%s create "
                   "push-pem" % (mastervol, user, slaveip, slavevol))
    else:
        if force:
            cmd = ("gluster volume geo-replication %s %s::%s create "
                   "push-pem force" % (mastervol, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s::%s create push-pem" %
                   (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_config_get(mnode, mastervol, slaveip, slavevol, config_key):
    """ All the available configurable geo-rep options can be got
        using the config_key and seeing what it has been set to

    Args:
        mnode (str) : Node on which cmd is to be executed
        mastervol (str) : The name of the mastervol
        slaveip (str): SlaveIP
        slavevol (str) The name of the slave volume
        config_key (str): The configurable options available in geo-replication
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution. In this case, it contains value of
            config.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = ("gluster volume geo-replication %s %s::%s config %s" %
           (mastervol, slaveip, slavevol, config_key))
    return g.run(mnode, cmd)


def georep_config_set(mnode, mastervol, slaveip, slavevol, config, value):
    """ All the available configurable geo-rep options can be set with a
        specific command if required or
        just with the config parameter
    Args:
        mnode (str) : Node on which cmd is to be executed
        mastervol (str) : The name of the mastervol
        slaveip (str): SlaveIP
        slavevol (str) The name of the slave volume
        config (str): The configurable options available in geo-replication
    Kwargs:
        value (str): The value for the geo-rep config
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    cmd = ("gluster volume geo-replication %s %s::%s config %s %s" %
           (mastervol, slaveip, slavevol, config, value))
    return g.run(mnode, cmd)


def georep_start(mnode, mastervol, slaveip, slavevol, user=None, force=False):
    """Starts the Geo-replication session
    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol (str): The name of the slave volume

    kwargs:
        force (bool): If this option is set to True, then the geo-rep
            session will be started with the force option.
            If it is set to False, then the session will be started
            without the force option -- which is the default option
        user (str): If not set, the default is a root-user
            If specified, non-root user participates in the geo-rep
            session

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        if force:
            cmd = ("gluster volume geo-replication %s %s@%s::%s start force" %
                   (mastervol, user, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s@%s::%s start" %
                   (mastervol, user, slaveip, slavevol))
    else:
        if force:
            cmd = ("gluster volume geo-replication %s %s::%s start force" %
                   (mastervol, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s::%s start" %
                   (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_stop(mnode, mastervol, slaveip, slavevol, user=None, force=False):
    """Stops a geo-repication session

    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol (str): The name of the slave volume
    kwargs:
        force (bool): If this option is set to True, then the geo-rep
            session will be stopped with the force option.
            If it is set to False, then the session will be stopped
            without the force option --which is the default option
        user (str): If not set, the default is a root-user
            If specified, non-root user participates in the geo-rep
            session

    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        if force:
            cmd = ("gluster volume geo-replication %s %s@%s::%s stop force" %
                   (mastervol, user, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s@%s::%s stop" %
                   (mastervol, user, slaveip, slavevol))
    else:
        if force:
            cmd = ("gluster volume geo-replication %s %s::%s stop force" %
                   (mastervol, slaveip, slavevol))
        else:
            cmd = ("gluster volume geo-replication %s %s::%s stop" %
                   (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_pause(mnode, mastervol, slaveip, slavevol, user=None):
    """Pauses the geo-replication session
    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol (str): The name of the slave volume
    Kwargs:
        user (str): If not set, the default is a root-user
        If specified, non-root user participates in geo-rep
        session
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.
    """
    if user:
        cmd = ("gluster volume geo-replication %s %s@%s::%s pause" %
               (mastervol, user, slaveip, slavevol))
    else:
        cmd = ("gluster volume geo-replication %s %s::%s pause" %
               (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_resume(mnode, mastervol, slaveip, slavevol, user=None):
    """Resumes the geo-replication session
    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol (str): The name of the slave volume
    Kwargs:
        user (str): If not set, the default is a root-user
        If specified, non-root user participates in geo-rep
        session
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        cmd = ("gluster volume geo-replication %s %s@%s::%s resume" %
               (mastervol, user, slaveip, slavevol))
    else:
        cmd = ("gluster volume geo-replication %s %s::%s resume" %
               (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)


def georep_delete(mnode, mastervol, slaveip, slavevol, user=None):
    """Deletes the geo-replication session
    Args:
        mnode (str): Node on which cmd is to be executed
        mastervol (str):The name of the master volume
        slaveip (str): SlaveIP
        slavevol (str): The name of the slave volume
    Kwargs:
        user (str): If not set, the default is a root-user
            If specified, non-root user participates in geo-rep
            session
    Returns:
        tuple: Tuple containing three elements (ret, out, err).
            The first element 'ret' is of type 'int' and is the return value
            of command execution.

            The second element 'out' is of type 'str' and is the stdout value
            of the command execution.

            The third element 'err' is of type 'str' and is the stderr value
            of the command execution.

    """
    if user:
        cmd = ("gluster volume geo-replication %s %s@%s::%s delete" %
               (mastervol, user, slaveip, slavevol))
    else:
        cmd = ("gluster volume geo-replication %s %s::%s delete" %
               (mastervol, slaveip, slavevol))
    return g.run(mnode, cmd)
