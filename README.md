# Jarvis
My personal team of AI agents, built step by step. First agent: PaceSetter.

## Status
 In development. Version 1 (planning engine and command line tool) works; Versions 2 and 3 are planned.

## PaceSetter's job
PaceSetter plans my day so that my hardest work lands in my focus hours, nothing clashes, deadlines are met with time to spare, and I get warned early when things don’t fit

## Try it
Needs Python 3.10 or newer. Nothing to install.

My own settings, events and tasks stay on my laptop, so this repo comes with sample ones. From the Jarvis folder:

```
copy settings.example.json settings.json
copy events.example.json events.json
copy tasks.example.json tasks.json
python -m pacesetter brief 2026-10-26     # a day's plan, warnings and suggestions
python -m pacesetter page 2026-10-26      # the same day as a web page
python -m pacesetter tasks                # tasks and progress
python -m pacesetter --help               # every command
```

## On macOS or Linux, use `cp` instead of `copy`.

## What it needs to know
- Fixed Events Examples(Meetings, upcoming events) Details (Name, day, start, end, whether it repeats)
- Task (Finish client proposal) Details (Name, how long it takes, deadline, how important, how much focus it needs)
- Learn from what really happened: was each task done, and how long did it actually take.

## What it gives me
- clash warnings
- alternatives
- weekly targets
- Reminder of every session before it begins


## What it must never do
- It only uses the information I give it, never changes anything without my approval, and always speaks professionally.
- It never shares my information with any person or service, and my data stays on my laptop.

## My day (these are settings and will change)
- Wake: 08:00
- Sleep: 00:00
- Work: 09:00 to 16:00
- Lunch: 13:00 to 14:30
- Most focused: 09:30 to 12:00
- Lowest energy: 15:00 to 16:00
- Work days: Monday to Friday

## Design rules
- Nothing about my day is fixed in the code; it all lives in settings I can change.
- PaceSetter suggests; I approve.
- Editing and Deleting schedules should be suggested; I approve
- Daily time for a task = minutes left ÷ work days left before its deadline, at least 30 minutes.
- PaceSetter never assumes work was done; I tell it what I actually did.

## Version 1
- Timed day plan, clash warnings, alternatives
- Remembers my tasks and how much of each is done
- Gives unfinished tasks a daily session until their deadline

## Version 2: web interface
- An interactive page to plan my day, manage tasks, and edit my settings without code
- Demo mode with sample data, for presenting to clients
- My Python engine stays the same underneath

## Version 3
- Tell PaceSetter what to do in plain English, typed or spoken

## Later
- Online version for companies (logins, separate data, hosting)
- Weekly targets
- Reminders before each session
- Reading my calendar (calendar agent)