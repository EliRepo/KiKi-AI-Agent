# Compilar e verificar o pacote Windows

Requer Windows x64, Python 3.11+ com Tcl/Tk. Na raiz do checkout:

```powershell
python -m pip install -r requirements-build.txt
python -m scripts.build_windows
```

O resultado contém dist/KiKi/KiKi.exe, runtime em _internal, fontes/licenças, LEIA-ME.txt, ZIP versionado e SHA256SUMS.txt. Somente o código e recursos do pacote são coletados; bancos, preferências e modelos não entram no ZIP. O script recusa arquivos de dados conhecidos dentro do bundle. Pastas dist/build precisam estar dentro do projeto; não compile com uma instância do EXE antigo em uso.

Verificação automatizada, sem rede ou banco pessoal:

```powershell
$app = Start-Process -FilePath ./dist/KiKi/KiKi.exe -ArgumentList '--smoke-test', 'build/smoke-packaged.json' -Wait -PassThru -WindowStyle Hidden
Get-Content build/smoke-packaged.json
```

O modo de verificação inicializa Tkinter, as quatro páginas, fontes, SQLite em memória e uma ferramenta confirmada com dados fictícios. Ele fecha sozinho e retorna código zero somente quando a verificação passa. Isso valida o runtime incluído; não substitui teste de uso em outro equipamento.

O workflow Tests roda a matriz Windows/Linux em Python 3.11–3.13, compila no Windows e verifica o EXE antes de anexar o artifact. Tags v* também publicam uma prévia versionada no GitHub Releases. A publicação requer que toda a matriz passe. O pacote não tem assinatura digital própria. Binários são assets de release/artifacts, não arquivos versionados no Git.

Para rodar o código em Linux/macOS, instale Python e o Tcl/Tk compatível com o sistema e use python -m kiki. Somente o pacote Windows x64 é produzido nesta entrega; não se declara distribuição nativa validada em macOS.
