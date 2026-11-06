# Opening the study on your computer

To only read the results, nothing is needed: open
[`notebook/reproduce_results.ipynb`](../notebook/reproduce_results.ipynb) here on GitHub, or
`notebook/reproduce_results.html` in a browser after downloading.

To run it yourself, download the repository (green **Code** button, then **Download ZIP**), extract
the whole zip to a normal folder such as Documents, and use the launcher for your system.

| System | What to do |
| --- | --- |
| Windows | Double-click `launchers\open_on_windows.bat`. If Windows shows "Windows protected your PC", choose **More info**, then **Run anyway**. |
| macOS | Double-click `launchers/open_on_mac.command`. If macOS blocks it, open **System Settings > Privacy & Security** and choose **Open Anyway**. Alternatively, run the Linux command below in Terminal. |
| Linux | In a terminal, from the study's folder, run `bash launchers/open_on_mac_or_linux.sh`. |

The first time, the launcher downloads a private copy of Python and the study's packages, which needs
an internet connection. Later openings skip this step. The notebook then opens in your browser with
its results already showing; to re-run it, choose **Run > Run All Cells**. Keep the launcher's window
open while you work and close it when you finish.

**What it changes on your computer:** nothing outside the study's folder. It needs no administrator
rights and does not touch any Python you already have. To remove everything, delete the folder.

The launchers are plain text files that you can read before running them.
