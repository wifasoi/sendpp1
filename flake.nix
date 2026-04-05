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

        # ── async-property (not in nixpkgs) ─────────────────────────────
        async-property = python.pkgs.buildPythonPackage rec {
          pname = "async_property";
          version = "0.2.2";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/c7/80/9f608d13b4b3afcebd1dd13baf9551c95fc424d6390e4b1cfd7b1810cd06/async_property-0.2.2-py2.py3-none-any.whl";
            sha256 = "sha256-iSTXkrWEOZRTf47UERZXALJ7K9lmzvxNru/BJTRCqdc=";
          };
          doCheck = false;
        };

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
          pythonRelaxDeps = [ "pyside6" ];
          pythonRemoveDeps = [ "pyside6" ];
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
        packages = {
          default = sendpp1-tui;
          tui = sendpp1-tui;
          wireshark-plugin = sendpp1-wireshark;
        };
        devShells.default = pkgs.mkShell {
          name = "sendpp1-dev";
          packages = [
            pythonPkgs
            pkgs.uv
            pkgs.ruff
            pkgs.wireshark-cli
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.bluez
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
            export WIRESHARK_PLUGIN_DIR="$(pwd)/wireshark"
          '';
        };
      }
    );
}