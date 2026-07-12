Name:           bak
Version:        %{version}
Release:        1%{?dist}
Summary:        Утилита для создания .bak резервных копий файлов

License:        MIT
Group:          Applications/File

%description
bak — утилита командной строки для создания резервных .bak копий
одного или нескольких файлов. Поддерживает шаблоны (glob),
рекурсивный обход директорий и ротацию существующих .bak-файлов
с добавлением даты/времени в имя.

%prep

%build

%install
mkdir -p %{buildroot}/usr/local/bin
install -m 755 %{_sourcedir}/bak %{buildroot}/usr/local/bin/

%files
/usr/local/bin/bak

%changelog
* Mon Jan 01 2024 Developer <dev@example.com> - 1.0.0-1
- Initial release
