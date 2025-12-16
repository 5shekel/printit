
## printit
this was a fun experimante in the 2023 ccc camp, people printed a lot of stickers.

live at > https://print.tami.sh 

it currntly a mini obsession. it can do a few things and more to come.   
 * print images (dithered as its a b/w thing)
 * print labels, with QR codes if url provided
 * print masks for PCB DIY etching(!), use the transparent ones for best resualts (WIP)
 * print text2image using stable diffusion API
 * print cats

started as a fork of [brother_ql_web](https://github.com/pklaus/brother_ql_web) and his brother_ql [printer driver](https://github.com/matmair/brother_ql-inventree), this driver is maintained and developed by matmair 

network access by the openziti/zrok projects
### TBD
 * better text/label handeling
   * wrap text for printing paragraphs
   * rotate labels to print bigger stuff
 * ???
 * profit


![print station](./assets/station_sm.jpg)
### usage
added `streamlit`` to requirements.txt
```bash
pip install -r requirements.txt
streamlit run printit.py --server.port 8989
```

we use the [zrok.io](https://zrok.io/) to secure a static url. 
```
```bash
zrok reserve public 8989
zrok share reserved xxxxxx
```


### systemd
add you service to keep it alive. change `<user>` with your username. or any path to the printit folder.

create at `/etc/systemd/system/sticker_zrok.service`
```bash
[Unit]
Description=sticker factory
After=network.target

[Service]
ExecStart=/bin/bash -c 'source /home/<user>/printit/venv/bin/activate && streamlit run printit.py --server.port 8989'
WorkingDirectory=/home/<user>/printit
Environment="PATH=/home/devdesk/<user>/printit/venv/bin/python"
Restart=always
User=<user>
Group=<user>
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl deamon-reload
sudo systemctl enable sticker.service
sudo systemctl start sticker.service

#debug using
sudo journalctl -u sticker.service --follow
sudo journalctl -u botprint.service --follow

```


we use the [zrok.io](https://docs.zrok.io/docs/guides/install/linux/) to secure a static url. 
```bash
zrok reserve public 8988
zrok share reserved kjvrml0bxatq
```
you can also run a service for this. 


### windows
to get the brother_ql lib to detect the printer, you need to install a usb filter 
 - grab release from [zdiag](https://zadig.akeo.ie/)
 - refresh device list
 - install the filter 'lib-winUSB` ,replacing the ql-XXXX driver
 - replug the printer


### update streamlit

streamlit had made some update with handling widths, `pip install --upgrade streamlit` if you see something in the line of 

```
Exception in tab Label: '<=' not supported between instances of 'str' and 'int'
Traceback (most recent call last):
  File "/home/pi/stikka-factory/printit.py", line 304, in <module>
    label_module.render(
  File "/home/pi/stikka-factory/tabs/label.py", line 256, in render
    st.image(img, width='stretch')
  File "/home/pi/printit/venv/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 410, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/pi/printit/venv/lib/python3.11/site-packages/streamlit/elements/image.py", line 154, in image
    WidthBehavior.ORIGINAL if (width is None or width <= 0) else width
``` 

## Refactoring Summary

### Configuration Management
- Created `config.toml` in workspace root for all application settings (non-sensitive)
- Moved settings from `secrets.toml` to `config.toml`: title, label_type, history_limit, items_per_page, queue_view, txt2img_url
- `secrets.toml` now contains only API keys (cat_api_key)

### Code Organization
- Extracted image processing utilities into `image_utils.py`
- Extracted printer handling utilities into `printer_utils.py`
- Updated `printit.py` to import from utility modules instead of defining functions locally

### UI/UX Improvements
- Updated all `st.image()` calls to use `use_container_width=True` for consistent responsive behavior, **updating streamlit is maybe needed**.

### Key Files Modified
- `config.toml` - Settings file
- `image_utils.py` - Image processing functions
- `printer_utils.py` - Printer handling functions
- `printit.py` - Main app (refactored)
- `tabs/*.py` - Tab modules (updated imports)

### Privacy mode
  - disables history tab
  - deletes labels