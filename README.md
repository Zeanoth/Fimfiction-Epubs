# Fimfiction-Epubs
For the maintenance of offline copies of fimfiction epubs.

<pre>
Features:
  Cover art is downloaded from https://www.fimfiction.net/ and added to the epub.</li>
  Border is added to cover art for quick reference to rating and completion status.</li>
  Description page is added to the beginning of the epub to include category information and story description.</li>

Required software:
  Python: <a href="https://www.python.org/downloads/">https://www.python.org/downloads/</a>
  OpenCV: <a href="http://docs.opencv.org/trunk/d5/de5/tutorial_py_setup_in_windows.html">http://docs.opencv.org/trunk/d5/de5/tutorial_py_setup_in_windows.html</a>
  Numpy: <a href="https://sourceforge.net/projects/numpy/files/NumPy/1.7.1/numpy-1.7.1-win32-superpack-python2.7.exe/download">https://sourceforge.net/projects/numpy/files/NumPy/1.7.1/numpy-1.7.1-win32-superpack-python2.7.exe/download</a>
  
How to use:
  Run main.py once to create the originals/ and updated/ folders.
  Download epubs from <a href="https://www.fimfiction.net/">https://www.fimfiction.net/</a> and copy them to the originals/ foler.
  Run main.py again to create updated versions of all epubs in the originals/ folder.
  Copy epubs from the updated/ folder onto device through preferred means.
  
How to add epub:
  Download epub from <a href="https://www.fimfiction.net/">https://www.fimfiction.net/</a> and copy to originals/ folder.
  Run main.py to created updated version in updated/ folder.
  
How to remove epub:
  Delete epub from originals/ folder and updated/ folder.
</pre>
