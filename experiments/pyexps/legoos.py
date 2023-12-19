# Copyright 2023 Max Planck Institute for Software Systems, and
# National University of Singapore
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''
Simple LegoOS experiment with a pComponent, a mComponent and a sComponent 
connected through ethernet.
'''
import math
import typing as tp

from simbricks.orchestration.experiment.experiment_environment import ExpEnv
from simbricks.orchestration.experiments import Experiment
from simbricks.orchestration.nodeconfig import NodeConfig, AppConfig
from simbricks.orchestration.simulators import QemuHost, E1000NIC, SwitchNet


class LegoOSNode(NodeConfig):

    def __init__(self) -> None:
        super().__init__()
        self.component = ''
        self.pcache_size_gb = 0

    def make_tar(self, path):
        pass

    def run_cmds(self) -> tp.List[str]:
        return []
    

class LegoOSModuleNode(NodeConfig):

    def __init__(self) -> None:
        super().__init__()
        self.disk_image = 'legoos'


class LegoOSModuleRunner(AppConfig):

    def __init__(self) -> None:
        super().__init__()
        self.module_list = []
        self.resource_list = []
        
    def config_files(self) -> tp.Dict[str, tp.IO]:
        file_dict = {}
        for module in self.module_list:
            file_dict[f'{module}.ko'] = open(f'../images/legoos/modules/{module}.ko', 'rb')
        for resource in self.resource_list:
            file_dict[resource] = open(f'../images/legoos/resources/{resource}', 'rb')
        return {**file_dict, **super().config_files()}
    
    def run_cmds(self, node: NodeConfig) -> tp.List[str]:
        cmds = []
        for module in self.module_list:
            cmds.append(f'insmod /tmp/guest/{module}.ko')
        cmds.append('sleep infinity')
        return cmds


class LegoOSHost(QemuHost):
    """Qemu host simulator for LegoOS kernel."""
    
    def __init__(self, node_config: LegoOSNode) -> None:
        super().__init__(node_config)

    def prep_cmds(self, env: ExpEnv) -> tp.List[str]:
        return []

    def run_cmd(self, env: ExpEnv) -> str:
        accel = ',accel=kvm:tcg' if not self.sync else ''
        if self.node_config.kcmd_append:
            kcmd_append = ' ' + self.node_config.kcmd_append
        else:
            kcmd_append = ''

        cmd = (
            f'{env.qemu_path} -machine q35{accel} -serial mon:stdio '
            '-cpu Skylake-Server -display none -nic none '
            f'-kernel {env.repodir}/images/legoos/{self.node_config.component} '
            f'-append "earlyprintk=ttyS0 console=ttyS0 {kcmd_append}" '
            f'-m {self.node_config.memory} -smp {self.node_config.cores} '
        )

        if self.sync:
            unit = self.cpu_freq[-3:]
            if unit.lower() == 'ghz':
                base = 0
            elif unit.lower() == 'mhz':
                base = 3
            else:
                raise ValueError('cpu frequency specified in unsupported unit')
            num = float(self.cpu_freq[:-3])
            shift = base - int(math.ceil(math.log(num, 2)))

            cmd += f' -icount shift={shift},sleep=off '

        for dev in self.pcidevs:
            cmd += f'-device simbricks-pci,socket={env.dev_pci_path(dev)}'
            if self.sync:
                cmd += ',sync=on'
                cmd += f',pci-latency={self.pci_latency}'
                cmd += f',sync-period={self.sync_period}'
            else:
                cmd += ',sync=off'
            cmd += ' '

        # qemu does not currently support net direct ports
        assert len(self.net_directs) == 0
        # qemu does not currently support mem device ports
        assert len(self.memdevs) == 0
        return cmd
    

e = Experiment(name='legoos')
e.checkpoint = True

# create pcomponent
pcomponent_config = LegoOSNode()
pcomponent_config.memory = '8G'
pcomponent_config.cores = 8
pcomponent_config.component = 'pcomponent'
pcomponent_config.kcmd_append = 'memmap=2G$4G'

pcomponent = LegoOSHost(pcomponent_config)
pcomponent.name = 'pcomponent'
pcomponent.wait = True
e.add_host(pcomponent)

# attach pcomponent's NIC
pcomponent_nic = E1000NIC()
e.add_nic(pcomponent_nic)
pcomponent.add_nic(pcomponent_nic)

# create mcomponent
mcomponent_config = LegoOSNode()
mcomponent_config.memory = '8G'
mcomponent_config.cores = 8
mcomponent_config.component = 'mcomponent'

mcomponent = LegoOSHost(mcomponent_config)
mcomponent.name = 'mcomponent'
e.add_host(mcomponent)

# attach mcomponent's NIC
mcomponent_nic = E1000NIC()
e.add_nic(mcomponent_nic)
mcomponent.add_nic(mcomponent_nic)

# create scomponent as a linux module
scomponent_app = LegoOSModuleRunner()
scomponent_app.module_list = ['ethfit', 'storage']
scomponent_app.resource_list = ['word_count', 'word.txt']

scomponent_config = LegoOSModuleNode()
scomponent_config.app = scomponent_app
scomponent_config.memory = '8G'
scomponent_config.cores = 8

scomponent = QemuHost(scomponent_config)
scomponent.name = 'scomponent'
e.add_host(scomponent)

# attach scomponent's NIC
scomponent_nic = E1000NIC()
e.add_nic(scomponent_nic)
scomponent.add_nic(scomponent_nic)

# connect NICs over network
network = SwitchNet()
e.add_network(network)
pcomponent_nic.set_network(network)
mcomponent_nic.set_network(network)
scomponent_nic.set_network(network)

experiments = [e]
