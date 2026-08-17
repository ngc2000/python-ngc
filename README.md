# python-ngc

An [agent skill](https://agentskills.io) that applies the NGC baseline — our
opinionated standard for private Python services and reusable libraries using uv.

## Install

Clone this repository into your user-level skills directory so agents can discover it:

```sh
git clone https://github.com/ngc2000/python-ngc.git ~/.agents/skills/python-ngc
```

On Windows PowerShell:

```powershell
git clone https://github.com/ngc2000/python-ngc.git "$HOME\.agents\skills\python-ngc"
```

For Claude Code, use `~/.claude/skills/python-ngc` instead. For a single project only, clone
into `<project>/.opencode/skill/python-ngc` (opencode) or `<project>/.claude/skills/python-ngc`.

Or if you would like to use a CLI:

```sh
npx skills add ngc2000/python-ngc
```

## Update

```sh
git -C ~/.agents/skills/python-ngc pull
```

With the CLI:

```sh
npx skills update python-ngc
```



## Usage

The skill activates only when you explicitly ask an agent to adopt or apply NGC to a
repository, e.g. "apply NGC to this project". It selects only the project profile and
capability guidance that matches the repository.
