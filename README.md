# NotCleo

These are Cogs designed to be used with [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot).
These Cogs were made primarily for use on the [King's Raid discord](https://discordapp.com/invite/kingsraid) as a replacement for both [KRBot](https://github.com/duckness/KRBot) and CleoBot. This is currently a WIP.

| Name   | Description                                                                                             |
| ------ | ------------------------------------------------------------------------------------------------------- |
| KRPlug | Relay announcements from plug.game to Discord.                                                          |
| KRinfo | Display info of various heroes, data from [Mask of Goblin](https://github.com/duckness/Mask-of-Goblin). |

## Installation

### Initial install

```
%load downloader
%repo add NotCleo https://github.com/duckness/NotCleo
%pipinstall bs4 parsedatetime pytz tzlocal
%cog install NotCleo <cogname>
%load <cogname>
```
### Updating

```
%cog update
```
## Usage