# PyEPL: convenience.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

"""
This module provides onvenience functions for writing experiments with
pyepl.
"""

import display
import sound
from keyboard import Key, KeyTrack
import joystick
from mouse import MouseRoller, MouseButton
import keyboard
import mechinput
import hardware
from textlog import LogTrack
import exputils

import math, numpy, pygame
import timing

# method for setting realtime
def setRealtime(period=120, computation=9600, constraint=1200):
    """
    Turns on realtime priority and attempts to keep the processor
    percentage below 100% so that the scheduler does not deplete the
    resources.  VR experiments tend to maintain too high use of the
    processor to make realtime worthwhile.

    You can optionally tweak the RT configuration with period,
    computation, and constraint as a function of the bus speed of the
    machine.  Be careful not to make the ratio between period and
    computation too large or you will prevent the sound from
    functioning properly.

    Please see this website for minimal details on RT priority on OSX:

    http://developer.apple.com/documentation/Darwin/Conceptual/KernelProgramming/scheduler/chapter_8_section_4.html
    
    """
    hardware.rt.set_realtime_priority(period,computation,constraint)
    hardware.eventpoll.isRealtime = 1

instructing = False

def getInstructing():
    global instructing
    return instructing

# Instruction functions:
def instructBegin(text, font = None, size = None, color = None, scroll = None, requireseenall = True, page_amount = None, scroll_speed = 0.2, leftmargin = 0.05, rightmargin = 0.05, topmargin = 0.05, justification = "LEFT"):
    """
    Initialize and draw the instruction text on the screen.  This
    function is normally called by the wrapper function instruct, but
    you could implement it on your own if needed.

    INPUT ARGS:
      (Please see the instruct method.)
    
    """
    # set up globals (used to remember status between insruct-related calls)...
    global inst_v
    global inst_resx
    global inst_resy
    global inst_font
    global inst_size
    global inst_color
    global inst_lines
    global inst_seenall
    global inst_position
    global inst_lastrend
    global inst_drawn
    global inst_scroll
    global inst_maxpos
    global inst_log
    global inst_topmargin
    global instructing
    
    assert not instructing, "instructBegin cannot be called while instructions are already shown"
    instructing = True
    
    # get the VideoTrack
    inst_v = display.VideoTrack.lastInstance()

    # get the screen resolution
    inst_resx, inst_resy = inst_v.getResolution()

    # calculate the top margin in pixels
    inst_topmargin = topmargin * inst_resy

    # use the font defaults where needed...
    if font:
        inst_font = font
    else:
        inst_font = display.defaultFont
    if size:
        inst_size = size
    else:
        inst_size = display.defaultFontSize
    if color:
        inst_color = color
    else:
        inst_color = display.defaultFontColor

    # use the font's wordWrap method to get a list of Text objects, each representing a line of text
    line_texts = inst_font.wordWrap(text, inst_size, inst_color, inst_resx - (inst_resy * (leftmargin + rightmargin)))

    # start with an empty list for 2-tuples of line Text objects and left padding amounts
    inst_lines = []

    # calculate left padding for each line...
    if justification == "LEFT":
        # if the justification is "left" put the left side of the texts at the left margin...
        for line_text in line_texts:
            inst_lines.append((line_text, leftmargin * inst_resy))
    elif justification == "RIGHT":
        # if the justification is "right" put the right side of the texts at the right margin...
        for line_text in line_texts:
            inst_lines.append((line_text, inst_resx - rightmargin * inst_resy - line_text.getSize()[0]))
    elif justification == "CENTER":
        # uf the justification is "center" center the texts between the margins...
        for line_text in line_texts:
            inst_lines.append((line_text, (leftmargin * inst_resy) + (inst_resx - (leftmargin + rightmargin) * inst_resy) / 2 - line_text.getSize()[0] / 2))
    
    # persistently load texts
    for line_text in line_texts:
        line_text.requireLoaded()

    # at start, the user has not seen all of the text
    inst_seenall = False

    # we start with position 0.0 at the top of the screen
    inst_position = 0.0

    # last position rendered starts as -1 (nothing rendered yet)
    inst_lastrend = -1

    # start with nothing drawn on the screen
    inst_drawn = []

    # if scroll is not given, create our own roller...
    if scroll == None:
        if not page_amount:
            # if page amount is not given generate one based on the hight of the screen
            page_amount = inst_resy * 0.75

        # initialize a list of component scollers to empty
        scrollers = []

        # append a vertical mouse roller
        scrollers.append(MouseRoller(1))

        # append the keyboard paging controls
        scrollers.append(mechinput.NotchRoller((Key("PAGE UP"), -page_amount),
                                               (Key("PAGE DOWN"), page_amount),
                                               (Key("SPACE"), page_amount)))

        # append the keyboard smooth scrolling
        scrollers.append(mechinput.ButtonRoller(Key("DOWN"), Key("UP"), scroll_speed))

        # append the joystick speed controlled scrolling
        scrollers.append(mechinput.AxisRoller(joystick.JoyAxis(0, 1)))

        # put all those rollers together
        inst_scroll = mechinput.JointRoller(*scrollers)
    else:
        # scroll was given, so just use it
        inst_scroll = scroll.echo()

    # we want to fill a screenfull before maxpos becomes positive
    inst_maxpos = -inst_resy + inst_topmargin

    for line, leftpadding in inst_lines:
        # increase maxpos by the vertical size of all the lines combined
        inst_maxpos += line.getSize()[1]

    # if maxpos is still negative (i.e. there was less than a screenfull)...
    if inst_maxpos < 0.0:
        # ...make it zero
        inst_maxpos = 0.0

    # create a log for the instructions
    inst_log = LogTrack("instruct")

    # mark the start of the instructions in the log
    inst_log.logMessage("INSTRUCTIONSTART\t%s\t%s\t%d\t%r\t%r" % (inst_scroll.name, inst_font.filename, int(inst_resy * inst_size), inst_color, text))

def instructStep():
    """
    This method waits for a keypress and will handle the scrolling of
    the instruction text.
    """
    # set up globals (used to remember status between insruct-related calls)...
    global inst_v
    global inst_resx
    global inst_resy
    global inst_font
    global inst_size
    global inst_color
    global inst_lines
    global inst_seenall
    global inst_position
    global inst_lastrend
    global inst_drawn
    global inst_scroll
    global inst_maxpos
    global inst_log
    global inst_topmargin

    # poll for events at each step
    hardware.pollEvents()

    # update position based on how much the scroll roller has moved
    inst_position += inst_scroll.getChange()

    # if position has become negative...
    if inst_position < 0.0:
        # ...clamp it to zero
        inst_position = 0.0
    # if it's gone above the maximum position...
    elif inst_position > inst_maxpos:
        # ...clamp it to the maximum position
        inst_position = inst_maxpos

    # we're at the maximum position...
    if inst_position == inst_maxpos:
        # ...then we've shown all the text - set seenall to True
        inst_seenall = True

    # round position to an integer for rendering
    thisrend = int(inst_position)

    # if the integer position (pixel position) has changed since the last step...
    if thisrend != inst_lastrend:
        # set lastrend to thisrend
        inst_lastrend = thisrend

        # unshow all the drawn text
        inst_v.unshow(*inst_drawn)

        # clear the drawn list
        inst_drawn = []

        # the top of the first line is thisrend pixels above the top of the screen
        index = -thisrend + inst_topmargin

        # iterate through the lines (Text objects)...
        for line, leftpadding in inst_lines:
            if index >= inst_resy:
                # if we've gone off the end of the screen, break the loop, since no more text will be visible
                break

            # get the height of the line
            lh = line.getSize()[1]

            # if the index is greater than minus the line height (i.e. if any part of the text is low enough to be visible)...
            if index > -lh:
                # show the line
                inst_drawn.append(inst_v.show(line, leftpadding, index))

            # increment index by the line height
            index += lh

        # update the screen, noting the timestamp
        timestamp = inst_v.updateScreen()

        # note the scrolling in the log
        inst_log.logMessage("INSTRUCTIONSCROLL\t%d" % thisrend, timestamp)

def instructSeenAll():
    """
    Return if they have seen all the instructions.
    """
    global inst_seenall

    # return the seenall global variable
    return inst_seenall

def instructEnd(exitbutton = None, clk = None):
    """
    Clean up after seeing all the instructions.

    INPUT ARGS:
      exitbutton- Optional exit button that was pressed.
      
    """
    # set up globals (used to remember status between insruct-related calls)...
    global inst_v
    global inst_resx
    global inst_resy
    global inst_font
    global inst_size
    global inst_color
    global inst_lines
    global inst_seenall
    global inst_position
    global inst_lastrend
    global inst_drawn
    global inst_scroll
    global inst_maxpos
    global inst_log
    global instructing

    # unshow all drawn text
    inst_v.unshow(*inst_drawn)
    
    # allow texts to be unloaded
    for line, leftpadding in inst_lines:
        line.unrequireLoaded()

    # update the screen, noting the timestamp
    timestamp = inst_v.updateScreen(clk)

    # tare the clock to the screen update time...
    # This is now done in the call to updateScreen
    #if clk:
    #    clk.tare(timestamp)
    
    if exitbutton:
        # if exitbutton is given, mark the end of the instructions in the log along with the exitbutton
        inst_log.logMessage("INSTRUCTIONSTOP\t%s" % exitbutton.name, timestamp)
    else:
        # otherwise, just mark the end of the instructions in the log
        inst_log.logMessage("INSTRUCTIONSTOP", timestamp)

    # clean up all the global variables used for instructions...
    del inst_v
    del inst_resx
    del inst_resy
    del inst_font
    del inst_size
    del inst_color
    del inst_lines
    del inst_seenall
    del inst_position
    del inst_lastrend
    del inst_drawn
    del inst_scroll
    del inst_maxpos
    del inst_log
    instructing = False

def instruct(text, font = None, size = None, color = None, scroll = None, exitbutton = None, requireseenall = True, pausevideolog = True, page_amount = None, scroll_speed = 0.2, leftmargin = 0.1, rightmargin = 0.1, topmargin = 0.1, justification = "LEFT", clk = None):
    """
    Display text on the screen, usually the instructions for your
    experiment.

    INPUT ARGS:
      text- Instructions to show.
      font/size/color- Font attibutes of the text
      scroll- Optional roller object to override keyboard scrolling.
      exitbutton- Optional alternative Button object used for exiting.
      requireseenall- False will let the user exit without viewing the
                      entire text.
      pausevideolog- False will continue to log all refreshes of the
                     screen during scrolling (It's usually good to keep
                     this as True).
      page_amount- Optionally indicate the number of pixels of displacement
                   for page ups and downs.
      scroll_speed- Optionally override the default scroll speed in pixels
                    per millisecond of scrolling with the up and down arrow
                    keys.
      leftmargin- left margin as a fraction of the height of the display.
      rightmargin- right margin as a fraction of the height of hte display.
      topmargin- top margin as a fraction of the height of the display.
      justification- Justification mode:
        "LEFT" - left justified
        "RIGHT" - right justified
        "CENTER" - centered
    """
    # set up globals (used to remember status between insruct-related calls)...
    #global inst_v
    #global inst_seenall

    # set up the instructions
    instructBegin(text, font, size, color, scroll, requireseenall, page_amount, scroll_speed)
    
    if exitbutton == None:
        # if the exit button is not given, use our own
        exitbutton = Key("RETURN") | joystick.JoyButton(0, 0) | MouseButton(0)

    # if we want to pause video logging...
    if pausevideolog:
        # remember whether or not it was logging already
        videowaslogging = inst_v.logall
        # stop the VideoTrack logging
        inst_v.stopLogging()

    # keep looping...
    #while True:
    #    if (inst_seenall or not requireseenall) and exitbutton.isPressed():
    #        # ...until the exit button is pressed and any seenall requirement is met
    #        break

    #    # do an instruction step at each iteration
    #    instructStep()
    
    inst_v.renderLoop(instructLoopCallback, requireseenall, exitbutton)

    if pausevideolog and videowaslogging:
        # unpause video logging
        inst_v.startLogging()

    # finalize the instrucitons
    instructEnd(exitbutton, clk = clk)

def instructLoopCallback(ts, requireseenall, exitbutton):
    # set up globals (used to remember status between insruct-related calls)...
    global inst_v
    global inst_seenall
    
    if (inst_seenall or not requireseenall) and exitbutton.isPressed():
        return False
    instructStep()
    return True

def waitForAnyKey(clk = None, showable = None, x = 0.5, y = 0.5, excludeKeys=None):
    """
    Wait for any key to be pressed.  Optionally you can pass in a
    showable to be displayed at the coordinants x,y.

    (Where is the Any key???)

    INPUT ARGS:
      clk- Optional PresentationClock for timing.
      showable- Text/Image object to display.
      x,y- Proportional coordinants of where to display the showable.
      excludeKeys- Optional keys to ignore, such as ['T','Q']
    """
    if excludeKeys: # decide which keys to wait for
        knames = []
        for kname in hardware.keyNames():
            if kname not in excludeKeys:
                knames.append(kname)
        
    # if a showable is given...
    if showable:
        # get the VideoTrack
        v = display.VideoTrack.lastInstance()
        
        # show the showable
        shown = v.showProportional(showable, x, y)

        # update the screen (using the clock object)
        v.updateScreen(clk)

    # get the keytrack
    k = KeyTrack.lastInstance()
    
    # wait for a key press
    if excludeKeys:
        bc = k.keyChooser(*knames)
    else:
        bc = k.keyChooser()
    but,timestamp = bc.waitWithTime(clock=clk)

    # if we displayed a showable...
    if showable:
        # ...unshow it
        v.unshow(shown)
        # and update the screen again
        v.updateScreen(clk)

    
def buttonChoice(clk = None, **buttons):
    """
    Wait for a combination of buttons, returning which one was
    pressed.  See the example below to see how to use it.

    INPUT ARGS:
      clk- Optional PresentationClock for timing.
      **buttons- Keyword args, where the arg. name is the name
                 for the button and the arg is the button itself.

    EXAMPLE:

    response = buttonChoice(clk=clock, yes=Key('Y'), no=Key('N'))
    if response == "yes"
       # they pressed Y
       pass
    else
       # the pressed N
       pass
    """
    # wait for one of the buttons to be pressed
    button, timestamp = mechinput.ButtonChooser(*buttons.values()).waitWithTime(clock=clk)

    # iterate over the keyword arguments searching for the button that was pressed...
    for key, value in buttons.items():
        # when we find it...
        if value is button:
            # ...return the keyword name
            return key


def micTest(recDuration = 2000, ampFactor = 1.0, clk = None, excludeKeys=None):
    """
    Microphone test function.  Requires VideoTrack, AudioTrack,
    KeyTrack to already exist.

    INPUT ARGS:
      recDuration- Duration to record during the test.
      ampFactor- Amplification factor for playback of the sound.
      clk- Optional PresentationClock for timing.

    OUTPUT ARGS:
      status- True if you should continue the experiment.
              False if the sound was not good and you should
              quit the program.
    """

    v = display.VideoTrack.lastInstance()
    a = sound.AudioTrack.lastInstance()
    k = keyboard.KeyTrack.lastInstance()
    
    if clk is None:
        clk = exputils.PresentationClock()
    
    done = False
    while not done:
        v.clear()
        v.showProportional(display.Text("Microphone Test",size = .1), .5, .1)
        waitForAnyKey(clk,showable=display.Text("Press any key to\nrecord a sound after the beep."), excludeKeys=excludeKeys)

        # clear screen and say recording
	beep1 = sound.Beep(400, 500, 100)
	beep1.present(clk)

        t = v.showCentered(display.Text("Recording...",color=(1,0,0)))
        v.updateScreen(clk)
        (testsnd,x) = a.record(recDuration, t=clk)
        v.unshow(t)
        v.updateScreen(clk)

        # play sound
        t = v.showCentered(display.Text("Playing..."))
        v.updateScreen(clk)
        a.play(testsnd,t=clk, ampFactor=ampFactor)
        v.unshow(t)
        v.updateScreen(clk)
        
        # ask if they were happy with the sound
        t = v.showCentered(display.Text("Did you hear the recording?"))
        v.showRelative(display.Text("(Y=Continue / N=Try Again / C=Cancel)"),display.BELOW,t)
        v.updateScreen(clk)

        response = buttonChoice(clk,
                                yes = (Key('Y') | Key('RETURN')),
                                no = Key('N'),
                                cancel = Key('C'))
        status = True
        if response == "cancel":
            status = False
        elif response == "no":
            # do it again
            continue
        done = True

    # clear before returning
    v.clear()
        
    return status


def presentStimuli(stimuli, attribute, duration, clk = None, on_jitter = None, ISI = None, ISI_jitter = None):
    """
    Present stimuli using their default present method.

    INPUT ARGS:
      stimuli- A Pool of stimuli to present.
      attribute- The attribute to present, like 'image',
                 'sound', or 'stimtext'
      duration/on_jitter- The duration to display the stimulus.
      ISI/ISI_jitter- The blank ISI between stimuli.
    """

    if clk is None:
        clk = exputils.PresentationClock()
    
    # loop over the stimuli
    for stim in stimuli.iterAttr(attribute):
        # show the stimuli
        stim.present(clk, duration, on_jitter)

        # do the isi between stimuli
        if ISI is not None:
            clk.delay(ISI,ISI_jitter)

        
def flashStimulus(showable, duration = 1000, x = 0.5, y = 0.5, jitter = None, clk = None):
    """
    Flash a showable on the screen for a specified duration.

    INPUT ARGS:
      showable- Object to display.
      duration- Duration to display the image.
      x,y- Location of the showable.
      jitter- Amount to jitter the presentation duration.
      clk- PresentationClock for timing.

    OUTPUT ARGS:
      timestamp- Time/latency when stimulus was presented on the screen.
    """
    if clk is None:
        # if no PresentationClock is given, create one
        clk = exputils.PresentationClock()

    # get the VideoTrack
    v = display.VideoTrack.lastInstance()

    # show the stimulus
    shown = v.showProportional(showable, x, y)

    # update the screen
    timestamp = v.updateScreen(clk)

    # delay
    clk.delay(duration, jitter)

    # unshow the stimulus
    v.unshow(shown)

    # update the screen
    v.updateScreen(clk)

    # return ontime
    return timestamp

def recognition(targets,lures,attribute,
                clk = None,
                log = None,
                duration = None,
                jitter = None,
                minDuration = None,
                ISI = None,
                ISI_jitter = None,
                targetKey = "RCTRL",
                lureKey = "LCTRL",
                judgeRange = None):
    """
    Run a generic recognition task.  You supply the targets and lures
    as Pools, which get randomized and presented one at a time
    awaiting a user response.  The attribute defines which present
    method is used, such as image, sound, or stimtext

    This function generates two types of log lines, one for the
    presentation (RECOG_PRES) and the other for the response
    (RECOG_RESP).  The columns in the log files are as follows:

    RECOG_PRES -> ms_time, max dev., RECOG_PRES, Pres_type, What_present, isTarget
    RECOG_RESP -> ms_time, max dev., RECOG_RESP, key_pressed, RT, max dev. isCorrect

    INPUT ARGS:
      targets- Pool of targets.
      lures- Pool of lures.
      attribute- String representing the Pool attribute to present.
      clk- Optional PresentationClock
      log- Log to put entries in.  If no log is specified, the method
           will log to recognition.log.
      duration/jitter- Passed into the attribute's present method.
           Jitter will be ignored since we wait for a keypress.
      minDuration- Passed into the present method as a min time they
                   must wait before providing a response.
      ISI/ISI_jitter- Blank ISI and jitter between stimuli, after
                   a response if given.
      targetKey- String representing the key representing targets.
      lureKey- String representing the key for the lure response.
      judgeRange- Tuple of strings representing keys for
                  confidence judgements.
                  If provided will replace targetKey and lureKey

    OUTPUT ARGS:


    TO DO:
    Try and see if mixed up the keys (lots wrong in a row)
    Pick percentage of targets from each list.
    
    """

    # get the tracks
    v = display.VideoTrack.lastInstance()
    a = sound.AudioTrack.lastInstance()
    k = keyboard.KeyTrack.lastInstance()

    # see if there is a presentation clock
    if not clk:
        clk = exputils.PresentationClock()

    # see if need logtrack
    if log is None:
        log = LogTrack('recognition')

    # Log start of recognition
    log.logMessage('RECOG_START')
    
    # add an attribute to keep track of them
    for stim in targets:
        stim.isTarget = True

    for stim in lures:
        stim.isTarget = False
    
    # concatenate the targets and lures
    stims = targets + lures

    # randomize them
    stims.shuffle()

    # make the ButtonChooser
    if not judgeRange:
        # use the target and lure keys provided
        bc = mechinput.ButtonChooser(Key(targetKey), Key(lureKey))
    else:
        # use the range
        #bc = mechinput.ButtonChooser(*map(lambda x: Key(str(x)), xrange(*judgeRange)))
        bc = mechinput.ButtonChooser(*map(Key,judgeRange))

    # delay before first stim if wanted
    if ISI:
        clk.delay(ISI,ISI_jitter)
     
    # present and wait for response
    for stim in stims:
        # optionally put answer choices up
        
        # present stimulus
        prestime,button,bc_time = getattr(stim,attribute).present(clk = clk,
                                                                  duration = duration,
                                                                  jitter = jitter,
                                                                  bc = bc,
                                                                  minDuration = minDuration)

        # clear the optional answer choices

        # see if target or not
        if stim.isTarget:
            isT = 1
        else:
            isT = 0
        
        # Process the response
        if button is None:
            # They did not respone in time
            # Must give message or something
            bname = "None"
            #isCorrect = -1
        else:
            # get the button name
            bname = button.name
            #isCorrect = -1
            
        # delay if wanted
        if ISI:
            clk.delay(ISI,ISI_jitter)
            
        # Log it, once for the presentation, one for the response
        log.logMessage('RECOG_PRES\t%s\t%s\t%d' %
                       (attribute,stim.name,isT),
                           prestime)
        log.logMessage('RECOG_RESP\t%s\t%ld\t%d' %
                       (bname,bc_time[0]-prestime[0],bc_time[1]+prestime[1]),bc_time)


    # Log end of recognition
    log.logMessage('RECOG_END')
    
    
def mathDistract(clk = None,
                 mathlog = None,
                 problemTimeLimit = None,
                 numVars = 2,
                 maxNum = 9,
                 minNum = 1,
                 maxProbs = 50,
                 plusAndMinus = False,
                 minDuration = 20000,
                 textSize = None,
                 correctBeepDur = 500,
                 correctBeepFreq = 400,
                 correctBeepRF = 50,
                 correctSndFile = None,
                 incorrectBeepDur = 500,
                 incorrectBeepFreq = 200,
                 incorrectBeepRF = 50,
                 incorrectSndFile = None,
                 tfKeys = None,
                 ansMod = [0,1,-1,10,-10],
                 ansProb = [.5,.125,.125,.125,.125],
		 visualFeedback = False):
    """
    Math distractor for specified period of time.  Logs to a math_distract.log
    if no log is passed in.

    INPUT ARGS:
      clk - Optional PresentationClock for timing.
      mathlog - Optional Logtrack for logging.
      problemTimeLimit - set this param for non-self-paced distractor;
                         buzzer sounds when time's up; you get at least
                         minDuration/problemTimeLimit problems.
      numVars - Number of variables in the problem.
      maxNum - Max possible number for each variable.
      minNum - Min possible number for each varialbe.
      maxProbs - Max number of problems.
      plusAndMinus - True will have both plus and minus.
      minDuration - Minimum duration of distractor.
      textSize - Vertical height of the text.
      correctBeepDur - Duration of correct beep.
      correctBeepFreq - Frequency of correct beep.
      correctBeepRF - Rise/Fall of correct beep.
      correctSndFile - Optional Audio clip to use for correct notification.
      incorrectBeepDur - Duration of incorrect beep.
      incorrectBeepFreq - Frequency of incorrect beep.
      incorrectBeepRF - Rise/Fall of incorrect beep
      incorrectSndFile - Optional AudioClip used for incorrect notification.
      tfKeys - Tuple of keys for true/false problems. e.g., tfKeys = ('T','F')
      ansMod - For True/False problems, the possible values to add to correct answer.
      ansProb - The probability of each modifer on ansMod (must add to 1).
      visualFeedback - Whether to provide visual feedback to indicate correctness.
    """

    # start the timing
    start_time = timing.now()

    # get the tracks
    v = display.VideoTrack.lastInstance()
    a = sound.AudioTrack.lastInstance()
    k = keyboard.KeyTrack.lastInstance()

    # see if need logtrack
    if mathlog is None:
        mathlog = LogTrack('math_distract')

    # log the start
    mathlog.logMessage('START')
    
    # start timing
    if clk is None:
        clk = exputils.PresentationClock()

    # set the stop time
    if not minDuration is None:
        stop_time = start_time + minDuration
    else:
        stop_time = None
    
    # generate the beeps
    correctBeep = sound.Beep(correctBeepFreq,correctBeepDur,correctBeepRF)
    incorrectBeep = sound.Beep(incorrectBeepFreq,incorrectBeepDur,incorrectBeepRF)
    
    # clear the screen (now left up to caller of function)
    #v.clear("black")

    # generate a bunch of math problems
    vars = numpy.random.randint(minNum,maxNum+1,[maxProbs, numVars])
    if plusAndMinus:
        pm = numpy.sign(numpy.random.uniform(-1,1,[maxProbs, numVars-1]))
    else:
        pm = numpy.ones([maxProbs, numVars-1])

    # see if T/F or numeric answers
    if isinstance(tfKeys,tuple):
        # do true/false problems
        tfProblems = True

        # check the ansMod and ansProb
        if len(ansMod) != len(ansProb):
            # raise error
            pass
        if sum(ansProb) != 1.0:
            # raise error
            pass
        ansProb = numpy.cumsum(ansProb)
    else:
	# not t/f problems 
        tfProblems = False

    # set up the answer button
    if tfProblems:
        # set up t/f keys
        ans_but = k.keyChooser(*tfKeys)
    else:
        # set up numeric entry
        ans_but = k.keyChooser('0','1','2','3','4','5','6','7','8','9','-','RETURN',
                               '[0]','[1]','[2]','[3]','[4]','[5]','[6]',
                               '[7]','[8]','[9]','[-]','ENTER','BACKSPACE')
    
    # do equations till the time is up
    curProb = 0
    while not (not stop_time is None and timing.now() >= stop_time) and curProb < maxProbs:
        # generate the string and result

        # loop over each variable to generate the problem
        probtxt = ''
        for i,x in enumerate(vars[curProb,:]):
            if i > 0:
                # add the sign
                if pm[curProb,i-1] > 0:
                    probtxt += ' + '
                else:
                    probtxt += ' - '

            # add the number
            probtxt += str(x)

        # calc the correct answer
        cor_ans = eval(probtxt)

        # add the equal sign
        probtxt += ' = '

        # do tf or numeric problem
        if tfProblems:
            # determine the displayed answer
            # see which answermod
            ansInd = numpy.nonzero(ansProb >= numpy.random.uniform(0,1))
            if isinstance(ansInd,tuple):
                ansInd = ansInd[0]
            ansInd = min(ansInd)
            disp_ans = cor_ans + ansMod[ansInd]

            # see if is True or False
            if disp_ans == cor_ans:
                # correct response is true
                corRsp = tfKeys[0]
            else:
                # correct response is false
                corRsp = tfKeys[1]

            # set response str
            rstr = str(disp_ans)
        else:
            rstr = ''

        # display it on the screen
        pt = v.showProportional(display.Text(probtxt,size = textSize),.4,.5)
        rt = v.showRelative(display.Text(rstr, size = textSize),display.RIGHT,pt)
        probstart = v.updateScreen(clk)
        
        # wait for input
        answer = .12345  # not an int
        hasMinus = False
	if problemTimeLimit:
	    probStart = timing.now()
	    probEnd = probStart + problemTimeLimit
	    curProbTimeLimit = probEnd - probStart
	else:
	    curProbTimeLimit = None

        # wait for keypress
        kret,timestamp = ans_but.waitWithTime(maxDuration = curProbTimeLimit, clock=clk)

        # process as T/F or as numeric answer
        if tfProblems:            
            # check the answer
            if not kret is None and kret.name == corRsp:
                isCorrect = 1
            else:
                isCorrect = 0
        else:
            # is part of numeric answer
            while kret and \
                      ((kret.name != "RETURN" and kret.name != "ENTER") or \
                       (hasMinus is True and len(rstr)<=1) or (len(rstr)==0)):
                # process the response
                if kret.name == 'BACKSPACE':
                    # remove last char
                    if len(rstr) > 0:
                        rstr = rstr[:-1]
                        if len(rstr) == 0:
                            hasMinus = False
                elif kret.name == '-' or kret.name == '[-]':
                    if len(rstr) == 0 and plusAndMinus:
                        # append it
                        rstr = '-'
                        hasMinus = True
                elif kret.name == 'RETURN' or kret.name == 'ENTER':
                    # ignore cause have minus without number
                    pass
                elif len(rstr) == 0 and (kret.name == '0' or kret.name == '[0]'):
                    # Can't start a number with 0, so pass
                    pass
                else:
                    # if its a number, just append
                    numstr = kret.name.strip('[]')
                    rstr = rstr + numstr

                # update the text
                rt = v.replace(rt,display.Text(rstr,size = textSize))
                v.updateScreen(clk)

                # wait for another response
                if problemTimeLimit:
                    curProbTimeLimit = probEnd - timing.now()
                else:
                    curProbTimeLimit = None
                kret,timestamp = ans_but.waitWithTime(maxDuration = curProbTimeLimit,clock=clk)

            # check the answer
            if len(rstr)==0 or eval(rstr) != cor_ans:
                isCorrect = 0
            else:
                isCorrect = 1

        # give feedback
        if isCorrect == 1:
	    # play the beep
            pTime = a.play(correctBeep,t=clk,doDelay=False)
	    #clk.tare(pTime[0])
            #correctBeep.present(clk)

	    # see if set color of text
	    if visualFeedback: 
		pt = v.replace(pt,display.Text(probtxt,size=textSize,color='green'))
		rt = v.replace(rt,display.Text(rstr, size=textSize, color='green'))
		v.updateScreen(clk)
		clk.delay(correctBeepDur)
        else:
	    # play the beep
            pTime = a.play(incorrectBeep,t=clk,doDelay=False)
	    #clk.tare(pTime[0])
            #incorrectBeep.present(clk)

	    # see if set color of text
	    if visualFeedback: 
		pt = v.replace(pt,display.Text(probtxt,size=textSize,color='red'))
		rt = v.replace(rt,display.Text(rstr, size=textSize, color='red'))
		v.updateScreen(clk)
		clk.delay(incorrectBeepDur)
        
        # calc the RT as (RT, maxlatency)
        prob_rt = (timestamp[0]-probstart[0],timestamp[1]+probstart[1])
        
        # log it
        # probstart, PROB, prob_txt, ans_txt, Correct(1/0), RT
        mathlog.logMessage('PROB\t%r\t%r\t%d\t%ld\t%d' %
                           (probtxt,rstr,isCorrect,prob_rt[0],prob_rt[1]),
                           probstart)
        
        # clear the problem
	v.unshow(pt,rt)
        v.updateScreen(clk)
        
        # increment the curprob
        curProb+=1

    # log the end
    mathlog.logMessage('STOP',timestamp)

    # tare the clock
    # PBS: Why set the time back to when the last button was pressed?
    #clk.tare(timestamp)

class StatusBar:
    """    
    Manages two rectangles, one drawn inside the other.  The inner
    rectange shrinks to show progress.  The recangles may be oriented
    vertically, in which case progress occurs from bottom to top, or
    horizontally, in which case progress occurs from right to left.
    """
    def __init__(self, width, height, startFraction=.5, totalSteps = 100, 
		 fullColor=(255, 255, 255), emptyColor=(0, 0, 0), fringeWidthPx=2):
	# do the full part
	self.fullDim = (width, height)
	self.fullColor = fullColor
	
	# do the empty part
	self.emptyDim = [0, 0]
	self.emptyOffset = [fringeWidthPx, fringeWidthPx]
	self.emptyColor = emptyColor
	self.fringeWidthPx = fringeWidthPx
	
	if width>height:
	    # it's horizontal
	    # assuming we fill from L to R
	    self.fillDimension = 0	    
	    self.staticDimension = 1
	else:
	    # it's vertical 
	    # assuming we fill bottom to top
	    self.fillDimension = 1
	    self.staticDimension = 0
    
	self.emptyDim[self.fillDimension] = int(self.fullDim[self.fillDimension]*startFraction - fringeWidthPx)
	self.emptyDim[self.staticDimension] = int(self.fullDim[self.staticDimension] - 2*fringeWidthPx)
	if self.fillDimension==0:	    
	    self.emptyOffset[self.fillDimension] = int(startFraction*
						  (self.fullDim[self.fillDimension] - 2*fringeWidthPx) + fringeWidthPx)

	self.pixelsPerStep = int(math.ceil((1-startFraction)*(self.fullDim[self.fillDimension] - 2*fringeWidthPx)/totalSteps))

    def getImage(self):
	# draw the larger rectangle
	self.fullSurf = pygame.Surface(self.fullDim)
	self.fullSurf.fill(self.fullColor)
	# draw the smaller rectangle
	self.emptySurf = pygame.Surface(tuple(self.emptyDim))
	self.emptySurf.fill(self.emptyColor)
	# superimpose the smaller one on the larger one
	self.fullSurf.blit(self.emptySurf, tuple(self.emptyOffset))
	return display.Image(hardware.graphics.LowImage(self.fullSurf))

    def increment(self, coefficient=1):
	# we always want to decrease emptyDim
	if self.emptyDim[self.fillDimension] > coefficient*self.pixelsPerStep and \
		self.emptyDim[self.fillDimension] < self.fullDim[self.fillDimension] - coefficient*self.pixelsPerStep:
	    self.emptyDim[self.fillDimension] -= coefficient*self.pixelsPerStep

	if self.fillDimension==0: 
	    # if it's horizontal, we also want to increase emptyOffset
	    if self.emptyOffset[self.fillDimension] < self.fullDim[self.fillDimension] - (self.fringeWidthPx + coefficeint*self.pixelsPerStep) and \
		    self.emptyOffset[self.fillDimension] > coefficient*self.pixelsPerStep:
		self.emptyOffset[self.fillDimension] += coefficient*self.pixelsPerStep
