# DREAMMATE

## _Make time and task management fun again!_

*DreamMate* is a tiny Python3 script utility that enables you to easily keep track of the time you spend on your daily job acitivies.

With a simple CLI it unifies the normal task and time management stuff in one single tool.

Designed with developers in mind, this tool can be adapted to work with everyone already familiar with the concept of *TODO task*, by using this concept as the building block of our time management strategy.

### The Idea

The design process behind DreamMate is very simple: whenever you start working on _something_ (let's keep this concept generic, for now), you simply need to start to keep track of the time you are spending on it.

So you can get over to the nearest terminal, and just type:
```
dm start <project_name>
```

Once you've done that, a Ledger CLI time entry has been generated in your `.config` folder.

All you need to do now is to start working on your activity.
When you finish your _current activity_ it's time to *commit* the work you've done.
This term is mutuated from the developer jargon, and it simply states that you're ready to save the work you've done by tagging it with a meaningful label describing the progress you've made in your project: the majority of time, this means that you actually *completed* a task, and thus the best method to put everything together is commiting you work with the task description as payload!

This is the core of everything in DreamMate, so please let me repeat it once again:

> DreamMate is designed to track your time by committing the task you accomplish.

### Installation

No package management has been setup yet. So you just need to have a working copy of Python3 on your system and you're ready to go.

Simply clone this repo and give execution permission to this file, then you can easily use dm as:
```
./dreammate.py --help
```

### Example usage

- **9.00**: You sit down in front of your computer, ready to make something incredible and meaningful right inside your NeoVim editor. (Vim 8 is ok too...)
 `dm start myawesomeproject`


- **10.15**: After more than 70 minutes of hard work, you've made all the way through a very though issue you were facing with some nasty CSS styling. So you are ready to commit your code. But what if you can commit **both** your code **and** your time journal you need to provide your employer for the monthly payroll? The answer is easy: *DreamMate*!
`dm commit "Nasty CSS Styling bug fixed"`

- **10.26**: You just finished you coffee break and you're ready to get back to work on `myawesomeproject` when one of your clients (the *scary* and *never happy* one) calls you yelling that he needs the WebAPI update you promised him 2 days before. Of course, this guys "rents" you hourly, so you need to keep track of the time you're spending on his tasks... Am I getting you hyped, am I?
`dm start scaryunhappyproject`

- **11.59**: The update took longer than expected, but now everything is setup and working. You're almost there for lunch, so what's let to do is to update the Ledger journal, commit the changes, write on Wrike, send an email to the boss with *detailed* reports... No more!
`dm commit "Update completed for the main platform"`

- **12.30**: It's time for the lunch! Just put everything in pause and see some reports today's work:
 `dm pause`
 `dm log myawesomeproject`
 `dm log scaryunhappyproject`

### Git Integration

TODO

### TodoTXT Integration

TODO

### Usage

```

dm <action> [<args>]

Available actions:
  start     Start tracking time for a given project
  pause     Pause current tracking by closing current time entry (with placeholder)
  commit    Ends currently open (last) time entry with the appropriate payload
  log       Get all time entries for a given project
```
