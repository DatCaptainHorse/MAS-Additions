# Changelog #
# 1.1.0 -> 1.2.0
# - Added MIDI message batching
# 1.0.0 -> 1.1.0
# - Added option for MIDI keymap starting point
# no version -> 1.0.0
# - Added version number
# - Using official Submod API
# - Threading for faster responsiveness
# - Only partially overrides default piano, easier to keep updated

# TODO: MIDI input picker "- Added MIDI input picker"
# TODO: Non-blocking MIDI keymap key picker

default persistent.submods_dathorse_MIDI_keymapKey = 65

init -990 python:
    store.mas_submod_utils.Submod(
        author="DatHorse",
        name="MIDI Support",
        description=(
            "Adds MIDI keyboard support to piano.\n"
        ),
        version="1.2.0",
        dependencies={
            "Monika After Story Module" : (None, None)
        },
        settings_pane="submods_dathorse_MIDI_settings_pane",
        version_updates={}
    )

init 811 python:
    import store
    class MIDI_PianoDisplayableOverride(PianoDisplayable):
        import time
        import pygame
        import threading
        import store.mas_piano_keys as mas_piano_keys
        def __init__(self, mode, pnml=None):
            MASM.sendData("MIDI_START")
            self.MIDILock = threading.Lock()
            self.MIDIThreadRun = threading.Event()
            self.MIDIthread = threading.Thread(target = self._MIDIcallback)
            self.MIDIthread.start()
            self.midiCBKeys = {}
            #self.mkeys = {}
            self.setMIDIkeymap(persistent.submods_dathorse_MIDI_keymapKey)
            super(MIDI_PianoDisplayableOverride, self).__init__(mode, pnml)

        def setMIDIkeymap(self, startKey):
            self.mkeys = {
                startKey: mas_piano_keys.F4,
                startKey + 1: mas_piano_keys.F4SH,
                startKey + 2: mas_piano_keys.G4,
                startKey + 3: mas_piano_keys.G4SH,
                startKey + 4: mas_piano_keys.A4,
                startKey + 5: mas_piano_keys.A4SH,
                startKey + 6: mas_piano_keys.B4,
                startKey + 7: mas_piano_keys.C5,
                startKey + 8: mas_piano_keys.C5SH,
                startKey + 9: mas_piano_keys.D5,
                startKey + 10: mas_piano_keys.D5SH,
                startKey + 11: mas_piano_keys.E5,
                startKey + 12: mas_piano_keys.F5,
                startKey + 13: mas_piano_keys.F5SH,
                startKey + 14: mas_piano_keys.G5,
                startKey + 15: mas_piano_keys.G5SH,
                startKey + 16: mas_piano_keys.A5,
                startKey + 17: mas_piano_keys.A5SH,
                startKey + 18: mas_piano_keys.B5,
                startKey + 19: mas_piano_keys.C6
            }

        def quitflow(self):
            MASM.sendData("MIDI_STOP")
            self.MIDIThreadRun.set()
            self.MIDIthread.join()
            renpy.music.set_volume(1.0, channel="audio") # Just in case
            return super(MIDI_PianoDisplayableOverride, self).quitflow()

        @staticmethod
        def _changeMIDIkeymapKey():
            MASM.sendData("MIDI_KEYMAPKEY")
            startTime = time.time()
            while MASM.isWorking() and time.time() - startTime < 5.0:
                if MASM.hasDataCheck("MIDI_KEY", int):
                    persistent.submods_dathorse_MIDI_keymapKey = MASM.hasDataValue("MIDI_KEY", defaultValue = 65)
                    break
                time.sleep(0.1)

        def _MIDIcallback(self):
            while not self.MIDIThreadRun.is_set():
                notes, batch = MASM.hasDataWith("MIDI_NOTES")
                if notes is not None and batch is not None and len(batch) > 0:
                    for msg, vel in batch:
                        splitted = msg.split(".")
                        if len(splitted) > 1:
                            m = self.mkeys.get(int(splitted[1]), None)
                            if m is not None:
                                k = self.live_keymap.get(m, None)
                                if k is not None:
                                    with self.MIDILock:
                                        self.midiCBKeys[k] = vel
                                    renpy.redraw(self, 0)
                else:
                    time.sleep(0) # Yield thread, can't sleep as it adds too much latency and timing is not stable
                            
        def render(self, ev, x, y, st):
            with self.MIDILock:
                for k, vel in self.midiCBKeys.viewitems():
                    if len(self.played) > self.KEY_LIMIT:
                        self.played = list()
                    elif st - self.prev_time >= self.ev_timeout:
                        self._timeoutFlow()
                    self.prev_time = st
                    if vel > 0:
                        if not self.pressed.get(k, True):
                            self.pressed[k] = True
                            self.note_hit = True
                            self.played.append(k)
                            if self.state == self.STATE_LISTEN:
                                self.stateListen(pygame.KEYDOWN, k)
                            elif self.state in self.POST_STATES:
                                self.statePost(pygame.KEYDOWN, k)
                            elif self.state in self.TRANS_POST_STATES:
                                self.stateWaitPost(pygame.KEYDOWN, k)
                            elif self.state in self.MATCH_STATES:
                                self.stateMatch(pygame.KEYDOWN, k)
    
                            renpy.music.set_volume(vel/127.0, channel="audio") # Works on per-sound basis
                            renpy.play(self.pkeys[k], channel="audio")
                            renpy.music.set_volume(1.0, channel="audio")
    
                    elif vel == 0:
                        if self.pressed.get(k, False):
                            self.pressed[k] = False
    
            return super(MIDI_PianoDisplayableOverride, self).render(ev, x, y, st)

    v_list = config.version.split("-")[0].split(".") # *yoink* Thanks Mlem laf :)
    v_list = [ int(x) for x in v_list ] # Convert to integers
    if v_list <= [ 0, 12, 99 ] and v_list >= [ 0, 12, 4 ]:
        mas_override_label("mas_piano_start", "submods_dathorse_MIDI_override_piano_start")
        mas_override_label("mas_piano_loopstart", "submods_dathorse_MIDI_override_piano_loopstart")
        mas_override_label("mas_piano_songchoice", "submods_dathorse_MIDI_override_piano_songchoice")
        mas_override_label("mas_piano_setupstart", "submods_dathorse_MIDI_override_piano_setupstart")
        mas_override_label("mas_piano_loopend", "submods_dathorse_MIDI_override_piano_loopend")

label submods_dathorse_MIDI_override_piano_start:
    $ import store.mas_piano_keys as mas_piano_keys
    $ pnmlLoadTuples()
    m 1hua "You want to play the piano?"

label submods_dathorse_MIDI_override_piano_loopstart:
    $ song_list,final_item = mas_piano_keys.getSongChoices()
    $ song_list.sort()
    $ play_mode = PianoDisplayable.MODE_FREE

label submods_dathorse_MIDI_override_piano_songchoice:
    $ pnml = None
    if len(song_list) > 0:
        m 1eua "Did you want to play a song or play on your own, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Did you want to play a song or play on your own, [player]?{fast}"
            "Play a song.":
                m "Which song would you like to play?" nointeract
                show monika at t21
                call screen mas_gen_scrollable_menu(song_list, mas_piano_keys.MENU_AREA, mas_piano_keys.MENU_XALIGN, final_item)
                show monika at t11
                $ pnml = _return
                if pnml:
                    m 1hua "I'm so excited to hear you play, [player]!"
                    $ play_mode = PianoDisplayable.MODE_SONG
                    jump submods_dathorse_MIDI_override_piano_setupstart
                else:
                    jump submods_dathorse_MIDI_override_piano_songchoice

            "On my own.":
                pass
            "Nevermind.":
                jump submods_dathorse_MIDI_override_piano_loopend
    m 1eua "Then play for me, [player]~"

label submods_dathorse_MIDI_override_piano_setupstart:
    show monika 1eua at t22
    python:
        disable_esc()
        mas_MUMURaiseShield()
    stop music
    
    $ piano_displayable_obj = MIDI_PianoDisplayableOverride(play_mode, pnml=pnml)
    $ ui.add(piano_displayable_obj)
    $ full_combo,is_win,is_practice,post_piano = ui.interact()
    $ ui.remove(piano_displayable_obj)
    $ del piano_displayable_obj
    
    $ mas_MUMUDropShield()
    $ enable_esc()
    $ mas_startup_song()
    $ pnmlSaveTuples()

    show monika 1hua at t11
    if full_combo and not persistent._mas_ever_won['piano']:
        $ persistent._mas_ever_won['piano'] = True

    if post_piano != "mas_piano_result_none":
        m 1eua "Would you like to play again?{nw}"
        $ _history_list.pop()
        menu:
            m "Would you like to play again?{fast}"
            "Yes.":
                jump submods_dathorse_MIDI_override_piano_loopstart
            "No.":
                pass

label submods_dathorse_MIDI_override_piano_loopend:
    return

screen submods_dathorse_MIDI_settings_pane():
    python:
        submods_screen = store.renpy.get_screen("submods", "screens")
        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)
        else:
            _tooltip = None

    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        hbox:
            if _tooltip:
                textbutton _("MIDI Starting key: {}".format(persistent.submods_dathorse_MIDI_keymapKey)):
                    action Function(MIDI_PianoDisplayableOverride._changeMIDIkeymapKey)
                    hovered SetField(_tooltip, "value", "Click to set the starting point for piano keys.\nMAS will freeze until MIDI key is pressed or 5 seconds have passed.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("MIDI Starting key: {}".format(persistent.submods_dathorse_MIDI_keymapKey)):
                    action Function(MIDI_PianoDisplayableOverride._changeMIDIkeymapKey)