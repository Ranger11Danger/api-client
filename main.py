#!/usr/bin/env python
# coding=utf-8

import functools
import sys
import requests
import json
import threading
from typing import (
    Any,
    List,
)

from cmd2 import (
    EightBitBg,
    EightBitFg,
    Fg,
    ansi,
    Cmd,
    Cmd2ArgumentParser,
    with_argparser
)
from cmd2.table_creator import (
    AlternatingTable,
    BorderedTable,
    Column,
    HorizontalAlignment,
    SimpleTable,
)

# Text styles used in the tables
bold_yellow = functools.partial(ansi.style, fg=Fg.LIGHT_YELLOW, bold=True)
blue = functools.partial(ansi.style, fg=Fg.LIGHT_BLUE)
green = functools.partial(ansi.style, fg=Fg.GREEN)



def ansi_print(text):
    """Wraps style_aware_write so style can be stripped if needed"""
    ansi.style_aware_write(sys.stdout, text + '\n\n')



class Node:
    def __init__(self):
        self.loaded_modules = []



class App(Cmd):
    available_modules = ["mod1", "mod2", "mod3"]
    default_prompt = "(api-cli) "
    prompt = default_prompt
    nodes = {}
    
    selected_node = None
    _stop_event = threading.Event()
    def __init__(self):
        super().__init__()
        del Cmd.do_edit
        del Cmd.do_shell
        del Cmd.do_macro
        del Cmd.do_alias
        del Cmd.do_shortcuts
        del Cmd.do_run_pyscript
        del Cmd.do_run_script
        del Cmd.do_history

    # Helper function for doing post requests
    def post(self, path, data):
        data = json.loads(
            requests.post(f"http://127.0.0.1:8080{path}", data=data).text
            )
        return data

    # Helper function for doing get requests
    def get(self, path, data):
        data = json.loads(
            requests.get(f"http://127.0.0.1:8080{path}", data=data).text
            )
        return data

    def update_prompt(self, prompt):
        def prompt_thread(prompt):
            while True:
                if self.terminal_lock.acquire(blocking=False):
                    self.async_update_prompt(prompt)
                    self.terminal_lock.release()
                    return
        t = threading.Thread(target=prompt_thread, args=[prompt])
        t.start()

    def do_show_nodes(self,args):
        """Show current Nodes"""
        data = self.get("/nodes", None)
        data_list: List[List[Any]] = list()
        for i in data:
            # Add this node to our global list of nodes
            if i["name"] not in self.nodes:
                self.nodes[i["name"]] = Node()
            # Add all the nodes to our table
            data_list.append([i["name"], i["id"]])
        
        # Generate out Cols
        columns: List[Column] = list()
        columns.append(Column("tag", width=20))
        columns.append(Column("uuid", width=20))
        # Build and print Table
        bt = BorderedTable(columns)
        table = bt.generate_table(data_list)
        ansi_print(table)


    select_parser = Cmd2ArgumentParser()
    select_parser.add_argument("tag", help="Node ID/Tag")
    # Function to switch what node we are interacting with
    @with_argparser(select_parser)
    def do_select(self,args):
        """Select a node to interact with"""
        if args.tag in self.nodes.keys():
            self.update_prompt(f"({args.tag}) ")
            self.selected_node = args.tag
        else:
            print(f"Unknown Node '{args.tag}'")

    # drop from current node
    def do_back(self, args):
        if self.selected_node == None:
            print("You have to select a node before you can go back :) (show_nodes)")
            return
        """Disconnect from current node"""
        self.update_prompt(self.default_prompt)

    # Get info on the current selected node
    def do_info(self, args):
        if self.selected_node == None:
            print("Please select a node (show_nodes)")
            return
        """Get info on the current node"""

    base_parser = Cmd2ArgumentParser()
    base_subparsers = base_parser.add_subparsers(title='subcommands', help='subcommand help')
    parser_foo = base_subparsers.add_parser("load", help='foo help')
    parser_foo.add_argument('module_name', type=str, help='name of module to load', choices=available_modules)
    # Load/View Modules
    @with_argparser(base_parser)
    def do_modules(self, args):
        """Load/View Modules"""
        if self.selected_node == None:
            print("Please select a node (show_nodes)")
            return
        try:
            if args.module_name:
                print(f"Loading Module {args.module_name}...")
                if args.module_name not in self.nodes[self.selected_node].loaded_modules:
                    self.nodes[self.selected_node].loaded_modules.append(args.module_name)
        except:  
            print("Installed Modules:")
            for mod in self.available_modules:
                if mod in self.nodes[self.selected_node].loaded_modules:
                    print(f'  [+] {mod}')
                else:
                    print(f'  [ ] {mod}')
        
    def do_upload(self, args):
        """Upload file to selected node"""
        if self.selected_node == None:
            print("Please select a node (show_nodes)")
            return

    def do_download(self, args):
        """Download file from selected node"""
        if self.selected_node == None:
            print("Please select a node (show_nodes)")
            return

    def do_exec(self, args):
        """Execute binary on node"""
        if self.selected_node == None:
            print("Please select a node (show_nodes)")
            return

if __name__ == '__main__':
    # Default to terminal mode so redirecting to a file won't include the ANSI style sequences
    ansi.allow_style = ansi.AllowStyle.TERMINAL
    import sys
    app = App()
    sys.exit(app.cmdloop())
    
