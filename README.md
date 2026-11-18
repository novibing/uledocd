# Unofficial LED OCD

Copyright (C) 2026 Stephen Jonke

This tool is open source and released under the GPL 3.0 license. Any modifications you may make to it must also be GPL 3.0 (or later) and open-source, if you decide to distribute your variant. See the included LICENSE file for details.

## What Is LED OCD?

**Comet Pinball**'s LED OCD is an awesome board for older pinball machines that makes LED bulbs behave like the incandencent bulbs that were originally in the games. LED bulps are much lower power, produce little heat and last much longer, but they have the trait that when they are turned on they immediately turn on full and when turned off they immediately turn off. Incandescent bulbs don't do this - they inherently ramp up and down and that gives a much more pleasing to the eye look.

The LED OCD board simulates this by ramping the LED bulbs up through 8 brightness levels, and then back down through those 8 steps, with a settable delay between levels. It looks amazing. Even just using it stock it will look so much better, but you can use their configuration software to customize the look, or compensate for a bulb that is not as bright or does not light well at lower brightnesses, etc. It also eliminates ghosting and flickering which LED bulbs are susceptible to.

You can get more information on and buy the LED OCD board from **Comet Pinball**'s website:

[Comet Pinball LED OCD](https://www.cometpinball.com/collections/led-ocd-boards)

## Unofficial LED OCD

Unfortunately Comet's configuration software for LED OCD is Windows-only and Intel-only and I have a M4 MacBook Air (and a Raspberry Pi). So I wrote my own configuration software for these boards, entirely in Python. It can be run on anything that has Python 3.10 or later and the **FTDI USB Serial Driver**. Any even semi-recent version of macOS, Linux or Windows has this driver built-in, and if not you can install it (see below). In the case of Linux, recent versions of Ubuntu have it. I am not sure about other flavors of Linux, but you can install it if needed.

I also made improvements to the tool, adding settings, making the window resizable, adding optional automatic backups and more. So even Windows users may want to give this a shot. And if your Windows box has an Arm64 processor, Comet's configuration software is Intel-only.

I also included a CLI tool to send commands to the board and receive replies. I used it in development. I provide it in case you want to play around with it, but most users will want to use the GUI.

## How To Install

To install **Unofficial LED OCD** enter the following command at the command-line/Terminal/Powershell:

    pip install --upgrade uledocd

If this complains that the environment is externally managed, then you need to create and use a virtual environment:

    python -m venv venv
    source venv/bin/activate
    pip install --upgrade uledocd

If there is an update and you wish to install it you don't need to make the venv again. Just skip the "python -m venv venv" step.

## How To Use

To launch **Unofficial LED OCD** activate the virtual environment if needed ("source venv/bin/activate") and then enter the following command at the command-line/Terminal/Powershell:

    uledocd

Once you have activated the venv (if you needed to use that), you can just run uledocd. You only need to activate if not already activated.

I made **Unofficial LED OCD** very similar, for the most part, to Comet's configuration software, so see their usage instructions for how to use it:

[LED OCD Usage Instructions](https://ledocd.com/usage_led.html)

You may want to look in the settings (the gear icon at the bottom right of the window) and adjust settings as desired. And keep an eye on the log window (also at the bottom right) as it will tell you things like warnings, errors and when and where a backup has been made. You can Import backups just like you do for Exported settings. In my tool if the log message is in black it was successful, warnings have a yellow color and errors are in red. Another difference is the Manual and Passthrough modes have pop-up windows with some explanation of their purpose and use. There are also tooltips for most controls.

## FTDI USB Serial Driver

Again, most even semi-recent versions of macOS, Linux and Windows have the **FTDI USB serial driver** built-in, so connect your computer to the board and then try running **Unofficial LED OCD**. Select the serial port (if needed), click the Connect button, and see if it works. If after connecting it reports the LED OCD firmware version, you are good to go. If it reports an error, first try the other possible ports (if any). If none of them work you can get the driver for your OS and processor on the FTDI website:

[FTDI USB Serial Driver Download](https://ftdichip.com/drivers/vcp-drivers/)

Install the driver as instructed - a reboot may be needed after installation - then try **Unofficial LED OCD** again.

## What About GI OCD?

The LED OCD board is for the controlled lamps. Their GI OCD board is for general illumination lamps. It's also amazing. **Unofficial LED OCD** is only for Comet's LED OCD board. But... I am working on **Unofficial GI OCD** now. Stay tuned.... For information on GI OCD and to purchase, see Comet's webpage for it:

[Comet Pinball GI OCD](https://www.cometpinball.com/products/led-ocd-boards-general-illumination)

## Was This Vibe Coded?

I made it a point to **not** vibe code any of **Unofficial LED OCD**. Could I have done it faster with help from AI? Probably, but I wanted to know everything about how it worked, and also this was just a fun project for me. Also for philosophical reasons.

## Contact

Hopefully you find this tool useful, and if not, or if there's anything you think needs to be improved, or if you find any bugs or just need help getting it running, please do contact me. You can reach me on [Bluesky](https://bsky.app/profile/novibing.bsky.social) [Reddit](https://www.reddit.com/u/novibing/) or via [Email](mailto:sjonke@gmail.com). Please note that most of my email is junk, so there's a decent chance I'll never see your message, buried alive among the junk mail quicksand - so contacting me on Bluesky or Reddit is preferred. I don't have an X account and I hope you don't either, but if you do I'm not going to fight you over it.
