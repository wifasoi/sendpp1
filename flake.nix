{
  description = "sendpp1 — Brother Skitch PP1 embroidery machine controller";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;

        # ── Python deps for the TUI (no Qt needed) ──────────────────────
        pythonPkgs = python.withPackages (ps: with ps; [
          bleak
          click
          loguru
          pyembroidery
          textual
          async-property
        ]);

        # ── sendpp1-tui package ─────────────────────────────────────────
        sendpp1-tui = python.pkgs.buildPythonApplication {
          pname = "sendpp1-tui";
          version = "0.1.0";
          pyproject = true;
          src = ./.;

          build-system = [ python.pkgs.setuptools python.pkgs.wheel ];

          dependencies = with python.pkgs; [
            bleak
            click
            loguru
            pyembroidery
            textual
            async-property
          ];

          # The GUI (pyside6) is optional and heavy — skip it for the TUI
          pythonRelaxDeps = [ "pyside6" ];
          pythonRemoveDeps = [ "pyside6" ];

          # Only install the TUI entry point
          postInstall = ''
            rm -f $out/bin/sendpp1-gui 2>/dev/null || true
          '';

          meta = {
            description = "TUI controller for the Brother Skitch PP1 embroidery machine";
            mainProgram = "sendpp1-tui";
          };
        };

        # ── Wireshark dissector plugin ──────────────────────────────────
        sendpp1-wireshark = pkgs.stdenv.mkDerivation {
          pname = "sendpp1-wireshark";
          version = "0.1.0";
          src = ./wireshark;

          installPhase = ''
            runHook preInstall
            mkdir -p $out/lib/wireshark/plugins
            cp sendpp1.lua $out/lib/wireshark/plugins/
            runHook postInstall
          '';

          meta = {
            description = "Wireshark Lua dissector for the PP1 BLE protocol";
          };
        };

      in {
        # ── Packages ────────────────────────────────────────────────────
        packages = {
          default = sendpp1-tui;
          tui = sendpp1-tui;
          wireshark-plugin = sendpp1-wireshark;
        };

        # ── Dev shell ───────────────────────────────────────────────────
        devShells.default = pkgs.mkShell {
          name = "sendpp1-dev";

          packages = [
            pythonPkgs
            pkgs.uv
            pkgs.ruff
            pkgs.wireshark-cli
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.bluez        # BLE stack (Linux only)
          ];

          shellHook = ''
            echo ""
            echo "  sendpp1 dev shell"
            echo "  Python: ${python.version}"
            echo ""
            echo "  Run the TUI:      python -m sendpp1.tui.app <file.pes>"
            echo "  Run tests:        pytest"
            echo "  Lint:             ruff check src/"
            echo "  Wireshark:        tshark (with PP1 dissector)"
            echo ""

            # Make the Wireshark dissector available
            export WIRESHARK_PLUGIN_DIR="$(pwd)/wireshark"
          '';
        };
      }
    );
}
