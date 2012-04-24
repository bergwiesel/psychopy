"""Basic functions, including timing, rush (imported), quit
"""
# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, time, threading
# always safe to call rush, even if its not going to do anything for a particular OS
from psychopy.platform_specific import rush
from psychopy import logging
import subprocess, shlex

runningThreads=[] # just for backwards compatibility?
pyoServers = []

try:
    import pyglet
    havePyglet = True
    checkPygletDuringWait = True # may not want to check, to preserve terminal window focus
except:
    havePyglet = False
    checkPygletDuringWait = False

def quit():
    """Close everything and exit nicely (ending the experiment)
    """
    #pygame.quit() #safe even if pygame was never initialised
    logging.flush()
    for thisThread in threading.enumerate():
        if hasattr(thisThread,'stop') and hasattr(thisThread,'running'):
            #this is one of our event threads - kill it and wait for success
            thisThread.stop()
            while thisThread.running==0:
                pass#wait until it has properly finished polling
    # could check serverCreated() serverBooted() but then need to import pyo
    # checking serverCreated() does not tell you whether it was shutdown or not
    for ps in pyoServers: # should only ever be one Server instance...
        ps.stop()
        wait(.25)
        ps.shutdown()
    sys.exit(0)#quits the python session entirely

#set the default timing mechanism
"""(The difference in default timer function is because on Windows,
clock() has microsecond granularity but time()'s granularity is 1/60th
of a second; on Unix, clock() has 1/100th of a second granularity and
time() is much more precise.  On Unix, clock() measures CPU time
rather than wall time.)"""
if sys.platform == 'win32':
    getTime = time.clock
else:
    getTime = time.time

class Clock:
    """A convenient class to keep track of time in your experiments.
    You can have as many independent clocks as you like (e.g. one
    to time responses, one to keep track of stimuli...)
    The clock is based on python.time.time() which is a sub-millisec
    timer on most machines. i.e. the times reported will be more
    accurate than you need!
    """
    def __init__(self):
        self.timeAtLastReset=getTime()#this is sub-millisec timer in python
    def getTime(self):
        """Returns the current time on this clock in secs (sub-ms precision)
        """
        return getTime()-self.timeAtLastReset
    def reset(self, newT=0.0):
        """Reset the time on the clock. With no args time will be
        set to zero. If a float is received this will be the new
        time on the clock
        """
        self.timeAtLastReset=getTime()+newT

def wait(secs, hogCPUperiod=0.2):
    """Wait for a given time period.

    If secs=10 and hogCPU=0.2 then for 9.8s python's time.sleep function will be used,
    which is not especially precise, but allows the cpu to perform housekeeping. In
    the final hogCPUperiod the more precise method of constantly polling the clock
    is used for greater precision.

    If you want to obtain key-presses during the wait, be sure to use pyglet and
    to hogCPU for the entire time, and then call event.getKeys() after calling core.wait()
    
    If you want to suppress checking for pyglet events during the wait, do this once:
        core.checkPygletDuringWait = False
    and from then on you can do
        core.wait(sec)
    This will preserve terminal-window focus during command line usage.
    """
    #initial relaxed period, using sleep (better for system resources etc)
    if secs>hogCPUperiod:
        time.sleep(secs-hogCPUperiod)
        secs=hogCPUperiod#only this much is now left

    #hog the cpu, checking time
    t0=getTime()
    while (getTime()-t0)<secs:
        if not (havePyglet and checkPygletDuringWait):
            continue
        #let's see if pyglet collected any event in meantime
        try:
            # this takes focus away from command line terminal window:
            pyglet.media.dispatch_events()#events for sounds/video should run independently of wait()
            wins = pyglet.window.get_platform().get_default_display().get_windows()
            for win in wins: win.dispatch_events()#pump events on pyglet windows
        except:
            pass #presumably not pyglet

def shellCall(shellCmd, stdin='', stderr=False):
    """Call a single system command with arguments, return its stdout.
    Returns stdout,stderr if stderr is True.
    Handles simple pipes, passing stdin to shellCmd (pipes are untested on windows)
    can accept string or list as the first argument
    """
    if type(shellCmd) == str:
        shellCmdList = shlex.split(shellCmd) # safely split into cmd+list-of-args, no pipes here
    elif type(shellCmd) == list: # handles whitespace in filenames
        shellCmdList = shellCmd
    else:
        return None, 'shellCmd requires a list or string'
    proc = subprocess.Popen(shellCmdList, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutData, stderrData = proc.communicate(stdin)
    del proc
    if stderr:
        return stdoutData.strip(), stderrData.strip()
    else:
        return stdoutData.strip()

