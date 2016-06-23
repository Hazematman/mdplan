import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import Gtk
from gi.repository import WebKit
from gi.repository.GdkPixbuf import Pixbuf
import markdown
import argparse
import os
import stat

appDesc = "Project planning tool created by Lucas Fryzek"
projectHelp = "Path of project to open"

# File tree code from:
# http://stackoverflow.com/questions/23433819/creating-a-simple-file-browser-using-python-and-gtktreeview
def populateFileTree(treeStore, path, parent=None):
    itemCounter = 0
    # iterate over the items in the path
    for item in os.listdir(path):
        # Get the absolute path of the item
        itemFullname = os.path.join(path, item)
        name, ext = os.path.splitext(itemFullname)
        # Extract metadata from the item
        itemMetaData = os.stat(itemFullname)
        # Determine if the item is a folder
        itemIsFolder = stat.S_ISDIR(itemMetaData.st_mode)
        # Generate an icon from the default icon theme
        itemIcon = Gtk.IconTheme.get_default().load_icon("folder" if itemIsFolder else "text-x-generic", 22, 0)
        # Append the item to the TreeStore
        if ext == ".md" or itemIsFolder:
            currentIter = treeStore.append(parent, [item, itemIcon, itemFullname])
        # add dummy if current item was a folder
        if itemIsFolder:
            treeStore.append(currentIter, [None, None, None])
        #increment the item counter
        itemCounter += 1
    # add the dummy node back if nothing was inserted before
    if itemCounter < 1:
        treeStore.append(parent, [None, None, None])

def onRowExpanded(treeView, treeIter, treePath):
    # get the associated model
    treeStore = treeView.get_model()
    # get the full path of the position
    newPath = treeStore.get_value(treeIter, 2)
    # populate the subtree on curent position
    populateFileTree(treeStore, newPath, treeIter)
    # remove the first child (dummy node)
    treeStore.remove(treeStore.iter_children(treeIter))

def onRowCollapsed(treeView, treeIter, treePath):
    # get the associated model
    treeStore = treeView.get_model()
    # get the iterator of the first child
    currentChildIter = treeStore.iter_children(treeIter)
    # loop as long as some childern exist
    while currentChildIter:
        # remove the first child
        treeStore.remove(currentChildIter)
        # refresh the iterator of the next child
        currentChildIter = treeStore.iter_children(treeIter)
    # append dummy node
    treeStore.append(treeIter, [None, None, None])

class Application:
    def __init__(self, project):
        self.project = project
        self.window = Gtk.Window()
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.resize(800, 600)

        hpan = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        # Create file tree view
        self.treestore = Gtk.TreeStore(str, Pixbuf, str)
        populateFileTree(self.treestore, project)
        self.treeview = Gtk.TreeView(self.treestore)

        treeViewCol = Gtk.TreeViewColumn("File")
        colCellText = Gtk.CellRendererText()
        colCellImg = Gtk.CellRendererPixbuf()

        treeViewCol.pack_start(colCellImg, False)
        treeViewCol.pack_start(colCellText, True)
        treeViewCol.add_attribute(colCellText, "text", 0)
        treeViewCol.add_attribute(colCellImg, "pixbuf", 1)

        self.treeview.append_column(treeViewCol)
        self.treeview.connect('row-expanded', onRowExpanded)
        self.treeview.connect('row-collapsed', onRowCollapsed)
        self.treeview.connect('row-activated', self.onRowActive)

        scrollViewFile = Gtk.ScrolledWindow()
        scrollViewFile.add(self.treeview)

        self.webview = WebKit.WebView()
        scrollViewWeb = Gtk.ScrolledWindow()
        scrollViewWeb.add(self.webview)

        hpan.add1(scrollViewFile)
        hpan.add2(scrollViewWeb)
        hpan.set_position(150)
        self.window.add(hpan)

        self.window.show_all()

    def onRowActive(self, treeView, path, column):
        selection = treeView.get_selection()

        model, pathlist = selection.get_selected_rows()
        for path in pathlist:
            treeIt = model.get_iter(path)
            fileName = model.get_value(treeIt, 2)
            name, ext = os.path.splitext(fileName)

            if ext != ".md":
                return

            data = ""
            with open(fileName, 'r') as file:
                data = file.read()

            mdtext = markdown.markdown(data)
            self.webview.load_html_string(mdtext, "file://{}".format(fileName))

    def run(self):
        Gtk.main()


def getArgs():
    parser = argparse.ArgumentParser(description=appDesc)
    parser.add_argument('project', metavar='path', help=projectHelp)

    return parser.parse_args()

if __name__ == "__main__":
    args = getArgs()
    app = Application(args.project)
    app.run()
