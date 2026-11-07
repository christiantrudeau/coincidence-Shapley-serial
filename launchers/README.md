# Opening the study on your computer

To only read the results, nothing is needed: open
[`notebook/reproduce_results.ipynb`](../notebook/reproduce_results.ipynb) here on GitHub, or
`notebook/reproduce_results.html` in a browser after downloading.

To run it yourself, download the repository (green **Code** button, then **Download ZIP**), extract
the whole zip to a normal folder such as Documents, and use the launcher for your system.

| System | What to do |
| --- | --- |
| Windows | Double-click `launchers\open_on_windows.bat`. If Windows shows "Windows protected your PC", choose **More info**, then **Run anyway**. |
| macOS | Double-click `launchers/open_on_mac.command`. macOS blocks it the first time, so follow [the steps below](#macos-step-by-step). |
| Linux | In a terminal, from the study's folder, run `bash launchers/open_on_mac_or_linux.sh`. |

The first time, the launcher downloads a private copy of Python and the study's packages, which needs
an internet connection. Later openings skip this step. The notebook then opens in your browser with
its results already showing; to re-run it, choose **Run > Run All Cells**. Keep the launcher's window
open while you work and close it when you finish.

**What it changes on your computer:** nothing outside the study's folder. It needs no administrator
rights and does not touch any Python you already have. To remove everything, delete the folder.

The launchers are plain text files that you can read before running them.

## macOS, step by step

macOS blocks the launcher the first time. This is expected: it is a script downloaded from the
internet, and it is not signed by a registered Apple developer. You allow it once for each downloaded
copy of the study, and later openings need only a double-click.

1. On the repository's main page, choose the green **Code** button, then **Download ZIP**.
2. Double-click the ZIP in your Downloads folder to extract it. If you want the study somewhere else,
   such as Documents, move the extracted folder now.
3. Open the extracted folder, open `launchers`, and double-click `open_on_mac.command`.
4. macOS shows a window titled **"open_on_mac.command" Not Opened**, saying that Apple could not verify
   that the file is free of malware. Choose **Done**, not **Move to Trash**.
5. Open **System Settings**, go to **Privacy & Security**, and scroll down until you see a message about
   `open_on_mac.command`. Choose **Open Anyway**.
6. If macOS asks you to confirm, choose **Open Anyway** again. It may ask for your Mac's password or Touch
   ID; this is macOS recording your choice. If nothing opens afterwards, double-click the file again.
7. A Terminal window opens and sets up the study, which needs an internet connection the first time.
   When it finishes, the notebook opens in your browser.
8. Keep the Terminal window open while you work, and close it when you finish.

If you chose **Move to Trash** by mistake, put the file back from the Trash or download the ZIP again.

You can also skip the double-click: open Terminal, go to the study's folder, and run
`bash launchers/open_on_mac_or_linux.sh`.
