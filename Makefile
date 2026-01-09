.PHONY: setup install install-dev install-llama download-model \
        chat eval eval-smoke build-index check \
        lint format test clean clean-all help

# ============================================================================
# Variables
# ============================================================================

PYTHON := uv run python
CMAKE := $(shell which cmake 2>/dev/null || echo /opt/homebrew/opt/cmake/bin/cmake)
# Use MacOSX15.5.sdk if available (MacOSX26 may have incomplete C++ headers)
SDKROOT := $(shell if [ -d "/Library/Developer/CommandLineTools/SDKs/MacOSX15.5.sdk" ]; then echo "/Library/Developer/CommandLineTools/SDKs/MacOSX15.5.sdk"; else xcrun --show-sdk-path; fi)

# llama.cpp (pinned revision for reproducibility)
LLAMA_REPO := https://github.com/ggerganov/llama.cpp.git
LLAMA_REV := b4823
LLAMA_DIR := vendor/llama.cpp
LLAMA_CLI := $(LLAMA_DIR)/build/bin/llama-cli

# Modèle GGUF
MODEL_REPO := Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF
MODEL_FILE := qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
MODEL_DIR := models
MODEL_PATH := $(MODEL_DIR)/$(MODEL_FILE)

# Couleurs
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

# ============================================================================
# Aide
# ============================================================================

help: ## Affiche cette aide
	@echo "$(GREEN)RustSensei$(NC) - Commandes disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-18s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Installation
# ============================================================================

setup: ## Installe les dépendances Python
	@echo "$(GREEN)Installation dépendances Python...$(NC)"
	uv sync
	@echo "$(GREEN)Done$(NC)"

install: setup ## Alias pour setup

install-dev: ## Installe les dépendances de dev
	@echo "$(GREEN)Installation dev...$(NC)"
	uv sync --extra dev
	@echo "$(GREEN)Done$(NC)"

install-llama: ## Clone et compile llama.cpp dans vendor/
	@echo "$(GREEN)Installation llama.cpp (rev: $(LLAMA_REV))...$(NC)"
	@mkdir -p vendor
	@if [ ! -d "$(LLAMA_DIR)" ]; then \
		echo "Clonage llama.cpp..."; \
		git clone $(LLAMA_REPO) $(LLAMA_DIR); \
	fi
	@echo "Checkout révision $(LLAMA_REV)..."
	@cd $(LLAMA_DIR) && git fetch --tags && git checkout $(LLAMA_REV)
	@echo "Compilation llama.cpp (Metal/MPS)..."
	@cd $(LLAMA_DIR) && \
		SDKROOT=$(SDKROOT) \
		CPLUS_INCLUDE_PATH=$(SDKROOT)/usr/include/c++/v1:$(SDKROOT)/usr/include \
		$(CMAKE) -B build \
			-DGGML_METAL=ON \
			-DCMAKE_OSX_SYSROOT=$(SDKROOT) \
			-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 \
			-DCMAKE_CXX_FLAGS="-isysroot $(SDKROOT) -I$(SDKROOT)/usr/include/c++/v1 -I$(SDKROOT)/usr/include" \
		&& $(CMAKE) --build build --config Release -j
	@if [ -f "$(LLAMA_CLI)" ]; then \
		echo "$(GREEN)llama-cli compilé: $(LLAMA_CLI)$(NC)"; \
		$(LLAMA_CLI) --version || true; \
	else \
		echo "$(RED)Erreur: llama-cli non trouvé$(NC)"; \
		exit 1; \
	fi

install-all: setup install-llama download-model ## Installe tout (Python + llama.cpp + modèle)
	@echo "$(GREEN)Installation complète terminée$(NC)"

# ============================================================================
# Modèle
# ============================================================================

download-model: ## Télécharge le modèle GGUF
	@echo "$(GREEN)Téléchargement $(MODEL_FILE)...$(NC)"
	@mkdir -p $(MODEL_DIR)
	@if [ -f "$(MODEL_PATH)" ]; then \
		echo "$(YELLOW)Modèle déjà présent: $(MODEL_PATH)$(NC)"; \
	else \
		$(PYTHON) -c "from huggingface_hub import hf_hub_download; \
			hf_hub_download('$(MODEL_REPO)', '$(MODEL_FILE)', local_dir='$(MODEL_DIR)')"; \
		echo "$(GREEN)Modèle téléchargé: $(MODEL_PATH)$(NC)"; \
	fi

# ============================================================================
# Vérifications
# ============================================================================

check: ## Vérifie que tout est prêt (llama-cli, modèle, deps, rustc)
	@echo "$(GREEN)Vérification de l'environnement...$(NC)"
	@echo ""
	@# llama-cli
	@if [ -f "$(LLAMA_CLI)" ]; then \
		echo "  [$(GREEN)OK$(NC)] llama-cli: $(LLAMA_CLI)"; \
	else \
		echo "  [$(RED)MISSING$(NC)] llama-cli -> make install-llama"; \
	fi
	@# Modèle GGUF
	@if [ -f "$(MODEL_PATH)" ]; then \
		echo "  [$(GREEN)OK$(NC)] Modèle GGUF: $(MODEL_PATH)"; \
	else \
		echo "  [$(RED)MISSING$(NC)] Modèle GGUF -> make download-model"; \
	fi
	@# Python deps
	@if uv run python -c "import rich, typer, yaml" 2>/dev/null; then \
		echo "  [$(GREEN)OK$(NC)] Python deps"; \
	else \
		echo "  [$(RED)MISSING$(NC)] Python deps -> make setup"; \
	fi
	@# rustc (optionnel)
	@if command -v rustc >/dev/null 2>&1; then \
		echo "  [$(GREEN)OK$(NC)] rustc: $$(rustc --version | head -c 30)"; \
	else \
		echo "  [$(YELLOW)OPTIONAL$(NC)] rustc non trouvé (pour eval compile)"; \
	fi
	@echo ""

# ============================================================================
# Utilisation
# ============================================================================

chat: ## Lance le chat interactif
	@if [ ! -f "$(LLAMA_CLI)" ]; then \
		echo "$(RED)llama-cli non trouvé. Lancez: make install-llama$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(MODEL_PATH)" ]; then \
		echo "$(RED)Modèle non trouvé. Lancez: make download-model$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) -m app.chat

chat-rag: ## Lance le chat avec RAG
	$(PYTHON) -m app.chat --rag

# ============================================================================
# Évaluation
# ============================================================================

eval: ## Évalue le modèle sur tous les prompts
	@if [ ! -f "$(LLAMA_CLI)" ] || [ ! -f "$(MODEL_PATH)" ]; then \
		echo "$(RED)Lancez d'abord: make install-all$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Évaluation...$(NC)"
	$(PYTHON) scripts/evaluate.py

eval-smoke: ## Test rapide (5 prompts)
	@echo "$(GREEN)Smoke test...$(NC)"
	$(PYTHON) scripts/evaluate.py --limit 5

# ============================================================================
# RAG
# ============================================================================

build-index: ## Construit l'index RAG
	@echo "$(GREEN)Construction index RAG...$(NC)"
	$(PYTHON) scripts/build_index.py

# ============================================================================
# Qualité
# ============================================================================

lint: ## Vérifie le code
	uv run ruff check app/ scripts/

format: ## Formate le code
	uv run ruff format app/ scripts/

test: ## Lance les tests
	uv run pytest tests/ -v

# ============================================================================
# Nettoyage
# ============================================================================

clean: ## Nettoie les fichiers temporaires
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	rm -rf app/__pycache__ scripts/__pycache__
	rm -rf .coverage htmlcov
	@echo "$(GREEN)Clean$(NC)"

clean-all: clean ## Nettoie tout (vendor, models, index)
	@echo "$(YELLOW)Suppression vendor/, models/, rag/index/...$(NC)"
	rm -rf vendor/ models/ rag/index/*.faiss rag/index/*.pkl
	@echo "$(GREEN)Clean all$(NC)"
