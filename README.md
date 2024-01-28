# Hello Fairy Home Assistant Integration  [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
This integration allows you to control your Hello Fairy lights with Home Assistant using Bluetooth.

## Installation (with HACS)
1. Go to Home Assistant > HACS > Integrations > Click on tree dot (on top right corner) > Custom repositories \
and fill :
   * **Repository** :  `Alwinator/ha-hello-fairy-integration`
   * **Category** : `Integration` 

2. Click on `ADD`, restart HA.

## Installation (manual)
1. Download last release.
2. Unzip `custom_components/hellofairy` folder into your HomeAssistant : `custom_components`
3. Restart HA

## Technical Information

Device Address: BE01C2F5-E31D-88CE-C2CA-1CE2736B9832

### Reverse Engineered Commands
#### Service 5833FF01-9B8B-5191-6142-22A4536EF123
Used for unknown

#### Service 49535343-40D6-0152-5348-9FAFD205E455
Used for unknown

#### Service 49535343-FE7D-4AE5-8FA9-9FAFD205E455
Used for commands

aa020101bb Turn device on
aa020100bb Turn device off

aa03070100a403a503e8bb Set color to light blue
aa0307010159027503e8bb Set color to pink
aa03070100000000038cbb Set color to white
aa030701001403e8038cbb Set color to orange

aa0307010000000001b0bb Set color to white with lower brightness

aa030701 00a403a503e8 bb


aa030903116403e8016803e8bb Enable music mode "Energy"
