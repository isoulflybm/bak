# bak — Makefile для сборки .deb и .rpm пакетов
# Требования: python3, pip (для PyInstaller), dpkg-dev (deb), rpm-build (rpm)

SHELL := /bin/bash

PROJECT   = bak
VERSION   = 1.0.0
SRC	   = src/bak.py
BUILD_DIR = build
DIST_DIR  = dist
INSTALL_BIN = /usr/local/bin

# Приведение uname -m к deb-архитектуре
UNAME_M   = $(shell uname -m)
ifeq ($(UNAME_M),x86_64)
	DEB_ARCH = amd64
else ifeq ($(UNAME_M),aarch64)
	DEB_ARCH = arm64
else
	DEB_ARCH = $(UNAME_M)
endif
# RPM использует родной uname -m (x86_64, aarch64 и т.д.)
RPM_ARCH  = $(UNAME_M)

# --- Единый бинарник через PyInstaller ---
.PHONY: bin
bin:
	@echo "=== Сборка бинарника через PyInstaller ==="
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	pip install pyinstaller
	pyinstaller --onefile --name $(PROJECT) $(SRC)
	@echo "Бинарник: dist/$(PROJECT)"

# --- DEB-пакет ---
.PHONY: deb
deb: bin
	@echo "=== Сборка .deb пакета (архитектура: $(DEB_ARCH)) ==="
	mkdir -p $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)/DEBIAN
	mkdir -p $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)$(INSTALL_BIN)
	cp $(DIST_DIR)/$(PROJECT) $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)$(INSTALL_BIN)/
	chmod 755 $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)$(INSTALL_BIN)/$(PROJECT)
	cat deb/control | sed 's/__VERSION__/$(VERSION)/g; s/__ARCH__/$(DEB_ARCH)/g' > $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)/DEBIAN/control
	dpkg-deb --build $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION)
	mv $(BUILD_DIR)/deb/$(PROJECT)-$(VERSION).deb $(DIST_DIR)/
	@echo "Пакет: dist/$(PROJECT)-$(VERSION).deb"

# --- RPM-пакет (требуется rpm-build) ---
.PHONY: rpm
rpm: bin
	@echo "=== Сборка .rpm пакета (архитектура: $(RPM_ARCH)) ==="
	mkdir -p $(BUILD_DIR)/rpm/BUILD
	mkdir -p $(BUILD_DIR)/rpm/RPMS
	mkdir -p $(BUILD_DIR)/rpm/SOURCES
	mkdir -p $(BUILD_DIR)/rpm/SPECS
	mkdir -p $(BUILD_DIR)/rpm/SRPMS
	cp $(DIST_DIR)/$(PROJECT) $(BUILD_DIR)/rpm/SOURCES/
	cp rpm/$(PROJECT).spec $(BUILD_DIR)/rpm/SPECS/
	(cd $(BUILD_DIR)/rpm && rpmbuild -bb \
		--define "_topdir $$(pwd)" \
		--define "version $(VERSION)" \
		--target $(RPM_ARCH) \
		SPECS/$(PROJECT).spec)
	find $(BUILD_DIR)/rpm/RPMS -name '*.rpm' -exec cp {} $(DIST_DIR)/ \;
	@echo "Пакет: $(DIST_DIR)/$(PROJECT)-$(VERSION)-*.rpm"

# --- Всё сразу ---
.PHONY: all
all: deb rpm

# --- Локальная установка ---
.PHONY: install
install: bin
	install -m 755 $(DIST_DIR)/$(PROJECT) $(INSTALL_BIN)/

.PHONY: uninstall
uninstall:
	rm -f $(INSTALL_BIN)/$(PROJECT)

# --- Очистка ---
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) *.spec *.pyc __pycache__
