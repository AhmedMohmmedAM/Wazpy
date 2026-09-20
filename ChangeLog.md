# Changelog

All notable changes to Wazpy are documented in this file.

## [0.1.0] - First public release

This is the first version of Wazpy.

- Initial Version

## [0.1.1] - Setup

Here you have an setup script to setup all NodeJS packages and checking if it's working

- Some changes in NodeJS like: _ensureDependencies to ensure all NodeJS package and install the right versions
- Fixed server.js crash when Python client disconnects: Added an error listener to the net server instance to capture ECONNRESET exceptions, preventing the Node.js process from crashing unexpectedly.