..
  Copyright 2022 Max Planck Institute for Software Systems, and
  National University of Singapore
..
  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:
..
  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.
..
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

.. _sec-orchestration-framework:

Orchestration Framework for Virtual Prototypes
**********************************************

SimBricks provides users with a powerful orchestration framework to programmatically define and configure virtual prototypes through Python scripts.
To do this, users leverage the `simbricks-orchestration` python package that offers an intuitive and flexible API, allowing for seamless virtual prototype configuration.

The orchestration framework package is divided into three modules that reflect SimBricks configuration abstractions, namely the :ref:`System Configuration <sec-orchestration-framework-sys-conf>`,
:ref:`Simulation Configuration <sec-orchestration-framework-sim-conf>`, and :ref:`Instantiation Configuration <sec-orchestration-framework-inst-conf>`:

- `simbricks.orchestration.system`: For defining the systems structure through components, interfaces, and channels.
- `simbricks.orchestration.simulation`: For assigning simulators to components and defining simulation behavior.
- `simbricks.orchestration.instantiation`: For configuring how and where the virtual prototype is executed.

Consequently, scripts written by users typically adopt a three-part structure corresponding to these abstractions.

We will now take a closer look at how the SimBricks orchestration framework works and examine some of its most important aspects in detail. 

.. _sec-orchestration-framework-sys-conf:

System Configuration 
==============================

The System Configuration defines the structure of the virtual prototype.
This structure typically reflects the structure of real physical systems and is organized similar.

The System Configuration does not specify how the system will be simulated (that means the System Configuration does not make any simulator choices).
Instead it only **defines the blueprint of the virtual prototype and thus what the simualted system should look like**.

The System Configuration makes use of three key concepts:

- **Components:** Represent compoenents of the virtual prototype, such as a Corundum NIC, a Linux-Host, or a Switch.
- **Interfaces:** Define intefaces between components through which they will comunicate. An Interface could e.g. be a PCIe interface or a Ethernet interface.
- **Channels:** Channels connect interfaces and act as communication paths. These Channels are later upon execution transformed into shared memory queues that link simulator instances.

.. System
.. ------------------------------

..
  System Configuration: The blueprint of the virtual prototype system, detailing its components and properties.
  Simulation Configuration: Instructions specifying how the system components are simulated.
  Instantiation Configuration: Runtime details, such as placement and execution parameters.

.. Components
.. ------------------------------

.. Interfaces
.. ------------------------------

.. Channels
.. ------------------------------

..
  NOTE: WHEN SPEAKING OF CHANNELS, MENTION THIS AND REFERENCE THE SYNCHRONIZATION SECTION!!!!!!!!!!!
    Link Latency and Sync period
        Most of the pre-defined simulators in orchestration/simulators.py provide an attribute for tuning link latencies and the synchronization period.
        Both are configured in nanoseconds and apply to the message flow from the configured simulator to connected ones.
        Some simulators have interfaces for different link types, for example, NIC simulators based on NICSim have a PCIe interface to connect to a host and an Ethernet link to connect to the network.
        The link latencies can then be configured individually per interface type.
        The synchronization period defines the simulator’s time between sending synchronization messages to connected simulators.
        Generally, for accurate simulations, you want to configure this to the same value as the link latency.
        This ensures an accurate simulation.
        With a lower value we don’t lose accuracy, but we send more synchronization messages than necessary.
        The other direction is also possible to increase simulation performance by trading-off accuracy using a higher setting.
        For more information, refer to the section on Synchronization in the Architectural Overview.


.. _sec-orchestration-framework-sim-conf:

Simulation Configuration
==============================

The Simulation Configuration determines how the Components from the System Configuration are simulated.
Therefore, the System Configuration must be defined beforehand. 
Once that is done, each Component is assigned to a specific simulator. For example:

- A Corundum NIC could be simulated by a behavioral C++ simulator or an RTL simulator such as `Verilator <https://www.veripool.org/verilator/>`_.
- A host could be simulated using `QEMU <https://www.qemu.org/>`_ or other full-system simulators like `gem5 <https://www.gem5.org/>`_.


.. _sec-orchestration-framework-inst-conf:

Instantiation Configuration
==============================

The Instantiation Configuration specifies how the virtual prototype is executed, including execution details such as:

- Choice of a Runner responsible for the execution of the virtual prototype.
- Specification of simulation Fragments, that can be distributed across multiple runners.
