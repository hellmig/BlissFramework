#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

from BlissFramework.Utils import Qt4_widget_colors
from BlissFramework.Qt4_BaseComponents import BlissWidget
from BlissFramework import Qt4_Icons

import types


__category__ = "Qt4_General"


class Qt4_ChannelLabel(QtGui.QLabel):
    def __init__(self, chanObject, *args):
        QtGui.QLabel.__init__(self, *args)

        self.chanObject = chanObject
        self.formatString = None
        self.oldValue = None

        chanObject.connectSignal("update", self.update_value)
        chanObject.connectSignal("connected", self.enable)
        chanObject.connectSignal("disconnected", self.disable)

        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setText('%s: -' % chanObject.userName())

    def update_value(self, value):
        #print 'updated value = ', value
        if value is None:
            self.setText('-')
            return
                
        if type(value) == types.FloatType or type(value) == types.IntType:
            if self.formatString is not None:
                self.setText('%s' % self.formatString % value)
            else:
                self.setText('%s' % str(value))
        elif type(value) == types.DictType:
            text = '<table>'
            for key, val in value.iteritems():
                text += '<tr><td>%s</td><td>%s</td></tr>' % (key, val)
            text+='</table>'
            self.setText(text)
        elif type(value) == types.StringType:
            self.setText('%s' % value)
        else:
            logging.getLogger().error('Cannot display variable value : unknown type %s', type(value))

        self.oldValue = value

    def set_number_format_string(self, format):
        self.formatString = format
        self.update_value(self.oldValue)

    def enable(self):
        self.setEnabled(True)

    def disable(self):
        self.setEnabled(False)


class Qt4_HorizontalSpacer(QtGui.QWidget):
    def __init__(self, *args):
       QtGui.QWidget.__init__(self, *args)
   
       self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)


class DummyCallable:
    def __call__(self, *args, **kwargs):
        pass


class Qt4_CommandButton(QtGui.QWidget):
    def __init__(self, cmdObject, *args):
        QtGui.QWidget.__init__(self, *args)
        
        self.cmdObject = cmdObject
        self.entryWidgets = {}
        self.arguments = cmdObject.getArguments()

        _main_layout = QtGui.QVBoxLayout()
        _main_layout.setSpacing(5)
        _main_layout.setMargin(0)
        self.setLayout(_main_layout)

        if len(self.arguments) > 0: 
            entryWidgetsGrid = QtGui.QGridLayout()
            entryWidgetsGrid.setSpacing(0)
            entryWidgetsGrid.setMargin(5)
            _main_layout.addLayout(entryWidgetsGrid)
  
            for row, args in enumerate(self.arguments):
                argname, argtype, onchange, valuefrom = args
                name_label = QtGui.QLabel("%s: " % argname)
                entryWidgetsGrid.addWidget(name_label, row, 0)
                #sep_label = QtGui.QLabel(' : ')
                #entryWidgetsGrid.addWidget(sep_label, row, 1)
                cmdobj = DummyCallable()
                chanobj = None
                if onchange is not None:
                    cmd, container_ref = onchange
                    container = container_ref()
                    if container is not None:
                        cmdobj = container.getCommandObject(cmd)
                if valuefrom is not None:
                    chan, container_ref = valuefrom
                    container = container_ref()
                    if container is not None:
                        chanobj = container.getChannelObject(chan)
                      
                if argtype == 'combo':
                    combobox = QtGui.QComboBox()
                    entryWidgetsGrid.addWidget(combobox, row, 2)
                    combobox._items = {}
                    for name, value in cmdObject.getComboArgumentItems(argname):
                        #combobox.insertItem(name)
                        combobox.addItem(name)
                        combobox._items[name]=value
                        
                        def activated(text, widget = combobox, cmdobj = cmdobj):
                            cmdobj(str(widget._items[str(text)]))
    
                        QtCore.QObject.connect(combobox, QtCore.SIGNAL("activated(const QString&)"), activated)
                    combobox._activated = activated   
                    def valuechanged(value, widget = combobox, chanobj = chanobj):
                        try:
                            for i in range(widget.count()):
                                if widget._items[str(widget.text(i))]==value:
                                    widget.setCurrentItem(i)
                                    break
                        except:
                            logging.getLogger().exception("%s: could not set item", self.name())
                    if chanobj is not None:
                        chanobj.connectSignal("update", valuechanged)
                    
                    combobox._valuechanged = valuechanged
                    self.entryWidgets[argname] = combobox 
                else:
                    lineedit = QtGui.QLineEdit('')
                    entryWidgetsGrid.addWidget(lineedit, row, 2)
                    def onreturnpressed(widget = lineedit, cmdobj = cmdobj):
                        cmdobj(str(widget.text()))
    
                    QtCore.QObject.connect(lineedit, QtCore.SIGNAL("returnPressed()"), onreturnpressed) 
                    def valuechanged(value, widget = lineedit, chanobj = chanobj):
                        try:
                            widget.setText(str(value))
                        except:
                            logging.getLogger().exception("%s: could not set text", self.name())
                    if chanobj is not None:
                        chanobj.connectSignal("update", valuechanged)
                    lineedit._valuechanged = valuechanged
                    lineedit._onreturnpressed = onreturnpressed
                    self.entryWidgets[argname]=lineedit
  
                self.entryWidgets[argname]._onchange = cmdobj
                self.entryWidgets[argname]._from = chanobj
        # cmdExecuteBox = QtGui.QHBoxLayout()
        # _main_layout.addLayout(cmdExecuteBox)
        # cmdExecuteBox.addWidget(Qt4_HorizontalSpacer())
        self.cmdExecute = QtGui.QToolButton()
        self.cmdExecute.setText(cmdObject.userName())
        self.cmdExecute.setUsesTextLabel(True)
        self.cmdExecute.setIcon(QtGui.QIcon(Qt4_Icons.load("launch")))
        self.cmdExecute.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.cmdExecute.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed))
        #cmdExecuteBox.addWidget(self.cmdExecute)
        _main_layout.addWidget(self.cmdExecute)
        #cmdExecuteBox.addWidget(Qt4_HorizontalSpacer())

        cmdObject.connectSignal("commandBeginWaitReply", self.command_launched)
        cmdObject.connectSignal('commandReplyArrived', self.command_reply_arrived)
        cmdObject.connectSignal('commandFailed', self.command_reply_arrived)
        cmdObject.connectSignal('commandAborted', self.command_reply_arrived)
        cmdObject.connectSignal('connected', self.connected)
        cmdObject.connectSignal('disconnected', self.disconnected)
        cmdObject.connectSignal('commandReady', self.enable_command)
        cmdObject.connectSignal('commandNotReady', self.disable_command)
        self.connect(self.cmdExecute, QtCore.SIGNAL('clicked()'), self.launch_command)

    def command_launched(self,*args):
        self.cmdExecute.setText("abort")
        self.cmdExecute.setIcon(QtGui.QIcon(Qt4_Icons.load("stop")))

    def command_reply_arrived(self, *args):
        self.enable_command()

    def enable_command(self):
        self.cmdExecute.setText(self.cmdObject.userName())
        self.cmdExecute.setEnabled(True)
        self.cmdExecute.setIcon(QtGui.QIcon(Qt4_Icons.load("launch")))

    def disable_command(self):
        if str(self.cmdExecute.text()) != 'abort':
            self.cmdExecute.setEnabled(False)

    def launch_command(self, *args):
        if str(self.cmdExecute.text()) == 'abort':
            self.cmdObject.abort()
        else:
            args = []
            for argName, argType, onChange, valueFrom in self.arguments:
                entryWidget = self.entryWidgets[argName]
                if argType == 'combo':
                    svalue = str(entryWidget.currentText())
                else:
                    svalue = str(entryWidget.text())

                if argType == 'float':
                    convertFunc = float
                elif argType == 'integer':
                    convertFunc = int
                elif argType == 'string':
                    convertFunc = str
                elif argType == 'combo':
                    convertFunc = lambda s: entryWidget._items[s]
                else:
                    QtGui.QMessageBox.warning(self, 'Bad argument type', 'Do not know how to convert %s to %s.' % (svalue, argType), QtGui.QMessageBox.Ok)
                    return

                try:
                    value = convertFunc(svalue)
                except ValueError:
                    QtGui.QMessageBox.warning(self, 'Invalid value', '%s is not a valid %s value.' % (svalue, argType), QtGui.QMessageBox.Ok)
                    return
                else:
                    args.append(value)
            self.cmdObject(*tuple(args))

    def disconnected(self):
        self.cmdExecute.setEnabled(False)

    def connected(self):
        self.cmdExecute.setEnabled(True)
        

class Qt4_CommandBrick(BlissWidget):
    def __init__(self, *args):
        BlissWidget.__init__(self, *args)
        
        self.addProperty('mnemonic', 'string')
        self.addProperty('numberFormatString', 'formatString', '+####.##')
        self.addProperty('title', 'string', '')
        self.addProperty('commands_channels', 'string', '', hidden = True)
 
        self.__brick_properties = self.propertyBag.properties.keys()
        self.__commands_channels = {}
        
        self.defineSlot("showBrick", ())

        self.hardwareObject = None

        self.cmdButtons = []
        self.channelLabels = []
        
        self.lblTitle = QtGui.QLabel(self)
        self.lblTitle.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        self.channelsBox = QtGui.QGridLayout()
        self.commandsBox = QtGui.QVBoxLayout()
        
        _main_layout = QtGui.QVBoxLayout()
        _main_layout.addWidget(self.lblTitle)
        _main_layout.addLayout(self.channelsBox)
        _main_layout.addLayout(self.commandsBox)
        self.setLayout(_main_layout)

    def showBrick(self, show):
        if show:
            self.show()
        else:
            self.hide()

    def run(self):
        self['commands_channels']=self['commands_channels']
        self.adjustSize()

    def setExpertMode(self, expert):
       for cmdbtn in self.cmdButtons:
           property = "[cmd] %s expert only" % cmdbtn.cmdObject.name()
           try:
               expert_only = self[property]
           except:
               continue
           else:
               if expert_only:
                   cmdbtn.setEnabled(expert)

    def propertyChanged(self, property, oldValue, newValue):
        if property == 'mnemonic':
            if self.hardwareObject is not None:
                if not self.isRunning():
                    # we are changing hardware object in Design mode
                    for propname in self.propertyBag.properties.keys():
                        if not propname in self.__brick_properties:
                            self.delProperty(propname)
                
                for cmdbtn in self.cmdButtons:
                    cmdbtn.close()
                self.cmdButtons = []
               
                for lblchan in self.channelLabels:
                    lblchan.close()
                self.channelLabels = []
                    
            self.hardwareObject = self.getHardwareObject(newValue)

            if self.hardwareObject is None:
                return

            if hasattr(self.hardwareObject, 'getChannels'):
                for row, chan in enumerate(self.hardwareObject.getChannels()):
                    new_label =  QtGui.QLabel('<nobr><b>%s</b></nobr>' % str(chan.name()))
                    self.channelLabels.append(new_label)
                    self.channelsBox.addWidget(new_label, row, 0)
                    self.channelLabels[-1].setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    new_label = Qt4_ChannelLabel(chan)
                    self.channelLabels.append(new_label)
                    self.channelsBox.addWidget(new_label, row, 1)
                    self.channelLabels[-1].set_number_format_string(self['numberFormatString'])
                    if not self.isRunning():
                        propname = "[channel] %s" % chan.name()
                        self.addProperty(propname, "boolean", True)
                        self.showProperty(chan.name())
                       
                    if chan.isConnected():
                        self.channelLabels[-1].enable()
                        self.channelLabels[-1].update_value(chan.getValue())
                    else:
                        self.channelLabels[-1].disable()
                    
                for cmd in self.hardwareObject.getCommands():
                    new_cmd_button = Qt4_CommandButton(cmd)
                    self.cmdButtons.append(new_cmd_button)
                    self.commandsBox.addWidget(new_cmd_button)
                    if not self.isRunning():
                        propname = "[cmd] %s" % cmd.name()
                        self.addProperty(propname, "boolean", True)
                        self.addProperty(propname+" expert only", "boolean", False)
                        self.showProperty(cmd.name())
                   
                    if cmd.isConnected():
                        self.cmdButtons[-1].connected()
                    else:
                        self.cmdButtons[-1].disconnected()
            else:
                self.hardwareObject = None
                logging.getLogger().error("%s: hardware object does not contain any command", ho.name())

            self["commands_channels"]=self["commands_channels"]
            
            self.adjustSize()
        elif property == 'numberFormatString':
            for i in range(len(self.channelLabels)):
                if i % 2:
                    self.channelLabels[i].set_number_format_string(self['numberFormatString'])
        elif property == 'title':
            if len(newValue) == 0:
                self.lblTitle.hide()
            else:
                self.lblTitle.show()
                self.lblTitle.setText(newValue)
            self.adjustSize()
        elif property == 'commands_channels': 
            try:
                self.__commands_channels = eval(newValue)
            except:
                return

            print self.__commands_channels

            for objname, cmdchan_info in self.__commands_channels.iteritems():
                try:
                    show, expert_only = cmdchan_info
                except:
                    # compatibility with old config.
                    show = cmdchan_info 

                for i in range(0, len(self.channelLabels), 2):
                    label, channel_label = self.channelLabels[i:i+2]
              
                    if channel_label.chanObject.name()==objname:
                        if show:
                            label.show()
                            channel_label.show()
                        else:
                            label.hide()
                            channel_label.hide()
                        self.getProperty("[channel] %s" % objname).setValue(show)
                for cmdbtn in self.cmdButtons:
                    if cmdbtn.cmdObject.name()==objname:
                        if show:
                            cmdbtn.show()
                        else:
                            cmdbtn.hide()

                        self.getProperty("[cmd] %s" % objname).setValue(show)
                        try:
                            self.getProperty("[cmd] %s expert only" % objname).setValue(expert_only)
                        except:
                            logging.getLogger().exception("fuck")

            self.propertyBag.updateEditor()
        else:
            try:
                #n = "".join(property.split()[1:])
                n = property[property.find(" ")+1:]
            except:
                return
            else:
                if n.endswith("expert only"):
                    n = n[:-12]
                    self.__commands_channels[n]=(self[property[:-12]], newValue)
                else: 
                    try:
                        self.__commands_channels[n] = (newValue, self[n+" expert only"])
                    except:
                        self.__commands_channels[n] = (newValue, False)

                self["commands_channels"] = str(self.__commands_channels)
                logging.getLogger().info("%s", self["commands_channels"])

