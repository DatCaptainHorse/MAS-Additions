
## Preferences screen ##########################################################
##
## The preferences screen allows the player to configure the game to better suit
## themselves.
##
## https://www.renpy.org/doc/html/screen_special.html#preferences

screen preferences():

    tag menu

    if renpy.mobile:
        $ cols = 2
    else:
        $ cols = 4

    default tooltip = Tooltip("")

    use game_menu(_("Settings"), scroll="viewport"):

        vbox:
            xoffset 50

            hbox:
                box_wrap True

                if renpy.variant("pc"):

                    vbox:
                        style_prefix "radio"
                        label _("Display")
                        textbutton _("Window") action Preference("display", "window")
                        textbutton _("Fullscreen") action Preference("display", "fullscreen")

#                vbox:
#                    style_prefix "check"
#                    label _("Skip")
#                    textbutton _("Unseen Text") action Preference("skip", "toggle")
#                    textbutton _("After Choices") action Preference("after choices", "toggle")
                    #textbutton _("Transitions") action InvertSelected(Preference("transitions", "toggle"))

                #Disable/Enable space animation AND lens flair in room
                vbox:
                    style_prefix "check"
                    label _("Graphics")
                    textbutton _("Disable Animation") action ToggleField(persistent, "_mas_disable_animations")
                    textbutton _("Change Renderer") action Function(renpy.call_in_new_context, "mas_gmenu_start")


                vbox:
                    style_prefix "check"
                    label _("Gameplay")
                    if persistent._mas_unstable_mode:
                        textbutton _("Unstable"):
                            action SetField(persistent, "_mas_unstable_mode", False)
                            selected persistent._mas_unstable_mode

                    else:
                        textbutton _("Unstable"):
                            action [Show(screen="dialog", message=layout.UNSTABLE, ok_action=Hide(screen="dialog")), SetField(persistent, "_mas_unstable_mode", True)]
                            selected persistent._mas_unstable_mode
                            hovered tooltip.Action(layout.MAS_TT_UNSTABLE)

                    textbutton _("Repeat Topics"):
                        action ToggleField(persistent,"_mas_enable_random_repeats", True, False)
                        hovered tooltip.Action(layout.MAS_TT_REPEAT)

                ## Additional vboxes of type "radio_pref" or "check_pref" can be
                ## added here, to add additional creator-defined preferences.
                vbox:
                    style_prefix "check"
                    label _(" ")
                    textbutton _("Sensitive Mode"):
                        action ToggleField(persistent, "_mas_sensitive_mode", True, False)
                        hovered tooltip.Action(layout.MAS_TT_SENS_MODE)

            null height (4 * gui.pref_spacing)

            hbox:
                style_prefix "slider"
                box_wrap True

                python:
                    ### random chatter preprocessing
                    if mas_randchat_prev != persistent._mas_randchat_freq:
                        # adjust the randoms if it changed
                        mas_randchat.adjustRandFreq(
                            persistent._mas_randchat_freq
                        )

                    # setup the display string
                    rc_display = mas_randchat.getRandChatDisp(
                        persistent._mas_randchat_freq
                    )

                    # setup previous values
                    mas_randchat_prev = persistent._mas_randchat_freq


                    ### sunrise / sunset preprocessing
                    # figure out which value is changing (if any)
                    if mas_suntime.change_state == mas_suntime.RISE_CHANGE:
                        # we are modifying sunrise

                        if mas_suntime.sunrise > mas_suntime.sunset:
                            # ensure sunset remains >= than sunrise
                            mas_suntime.sunset = mas_suntime.sunrise

                        if mas_sunrise_prev == mas_suntime.sunrise:
                            # if no change since previous, then switch state
                            mas_suntime.change_state = mas_suntime.NO_CHANGE

                        mas_sunrise_prev = mas_suntime.sunrise

                    elif mas_suntime.change_state == mas_suntime.SET_CHANGE:
                        # we are modifying sunset

                        if mas_suntime.sunset < mas_suntime.sunrise:
                            # ensure sunrise remains <= than sunset
                            mas_suntime.sunrise = mas_suntime.sunset

                        if mas_sunset_prev == mas_suntime.sunset:
                            # if no change since previous, then switch state
                            mas_suntime.change_state = mas_suntime.NO_CHANGE

                        mas_sunset_prev = mas_suntime.sunset
                    else:
                        # decide if we are modifying sunrise or sunset

                        if mas_sunrise_prev != mas_suntime.sunrise:
                            mas_suntime.change_state = mas_suntime.RISE_CHANGE

                        elif mas_sunset_prev != mas_suntime.sunset:
                            mas_suntime.change_state = mas_suntime.SET_CHANGE

                        # set previous values
                        mas_sunrise_prev = mas_suntime.sunrise
                        mas_sunset_prev = mas_suntime.sunset


                    ## prepreocess display time
                    persistent._mas_sunrise = mas_suntime.sunrise * 5
                    persistent._mas_sunset = mas_suntime.sunset * 5
                    sr_display = mas_cvToDHM(persistent._mas_sunrise)
                    ss_display = mas_cvToDHM(persistent._mas_sunset)

                vbox:

                    hbox:
                        label _("Sunrise   ")

                        # display time
                        label _("[[ " + sr_display + " ]")

                    bar value FieldValue(mas_suntime, "sunrise", range=mas_max_suntime, style="slider")


                    hbox:
                        label _("Sunset   ")

                        # display time
                        label _("[[ " + ss_display + " ]")

                    bar value FieldValue(mas_suntime, "sunset", range=mas_max_suntime, style="slider")


                vbox:

                    hbox:
                        label _("Random Chatter   ")

                        # display str
                        label _("[[ " + rc_display + " ]")

                    bar value FieldValue(persistent, "_mas_randchat_freq",
                    range=6, style="slider")

                    hbox:
                        label _("Ambient Volume")

                    bar value Preference("mixer amb volume")


                vbox:

                    label _("Text Speed")

                    #bar value Preference("text speed")
                    bar value FieldValue(_preferences, "text_cps", range=170, max_is_zero=False, style="slider", offset=30)

                    label _("Auto-Forward Time")

                    bar value Preference("auto-forward time")

                vbox:

                    if config.has_music:
                        label _("Music Volume")

                        hbox:
                            bar value Preference("music volume")

                    if config.has_sound:

                        label _("Sound Volume")

                        hbox:
                            bar value Preference("sound volume")

                            if config.sample_sound:
                                textbutton _("Test") action Play("sound", config.sample_sound)


                    if config.has_voice:
                        label _("Voice Volume")

                        hbox:
                            bar value Preference("voice volume")

                            if config.sample_voice:
                                textbutton _("Test") action Play("voice", config.sample_voice)

                    if config.has_music or config.has_sound or config.has_voice:
                        null height gui.pref_spacing

                        textbutton _("Mute All"):
                            action Preference("all mute", "toggle")
                            style "mute_all_button"


            hbox:
                textbutton _("Update Version"):
                    action Function(renpy.call_in_new_context, 'forced_update_now')
                    style "navigation_button"

                textbutton _("Import DDLC Save Data"):
                    action Function(renpy.call_in_new_context, 'import_ddlc_persistent_in_settings')
                    style "navigation_button"

                textbutton _("Addition Settings"):
                   action [Show('additions')]
                   style "navigation_button"


## MAS-Additions Screen ##############################################################
##
## Displays installed additions to Monika After Story with some options
##

define gui.list_additions_menu_button_width = 500
define gui.list_additions_menu_button_height = None
define gui.list_additions_menu_button_tile = False
define gui.list_additions_menu_button_borders = Borders(25, 5, 25, 5)

define gui.list_additions_menu_button_text_font = gui.default_font
define gui.list_additions_menu_button_text_size = gui.text_size
define gui.list_additions_menu_button_text_xalign = 0.0
define gui.list_additions_menu_button_text_idle_color = "#000"
define gui.list_additions_menu_button_text_hover_color = "#fa9"

style list_additions_menu_button is choice_button:
    properties gui.button_properties("list_additions_menu_button")

style additions_menu_button is confirm_button
style additions_menu_button_text is confirm_button_text

screen additions():
    ## Ignore input on other screens
    modal True
    zorder 150
    style_prefix "additions_menu"

    frame:
        hbox:
            xalign 0.5
            label _('MAS-Additions Settings')

        viewport:
            draggable True
            mousewheel True

            vbox:
                null height 50
                spacing 5
                for i_addTag, i_addName, i_addVer in additions:
                    text '[[{}] {} [[{}]'.format(i_addTag, i_addName, i_addVer)
                    text 'Enabled: {}'.format(additionIsEnabled(i_addTag))
                    textbutton 'Enable' action Function(enableAddition,i_addTag)
                    textbutton 'Disable' action Function(disableAddition,i_addTag)

        hbox:
            xalign 0.5
            yalign 1.0
            textbutton _("Close") action Hide("additions")
