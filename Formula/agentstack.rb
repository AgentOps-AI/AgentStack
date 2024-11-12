class Agentstack < Formula
  include Language::Python::Virtualenv

  desc 'The fastest way to build robust AI agents'
  homepage 'https://agentstack.sh/'
  version '0.1.8'
  license 'MIT'

  url 'https://files.pythonhosted.org/packages/40/3d/73d0e4300a69975d3738578503dc147afef6bfd2c64c6fad6755f28d9d3e/agentstack-0.1.8.tar.gz'
  sha256 '5c1417b85eeade13921b05385e25cd16c804fdd48d14cdf3779245384090db4c'

  depends_on 'python@3.11'

  resource 'arrow' do
    url 'https://files.pythonhosted.org/packages/2e/00/0f6e8fcdb23ea632c866620cc872729ff43ed91d284c866b515c6342b173/arrow-1.3.0.tar.gz'
    sha256 'd4540617648cb5f895730f1ad8c82a65f2dad0166f57b75f3ca54759c4d67a85'
  end

  resource 'art' do
    url 'https://files.pythonhosted.org/packages/f5/49/9d40caffc16ab712bef515afd19dc069d36c47c86ef54e22e73068cfcfea/art-6.3.tar.gz'
    sha256 '0fbc28864583ba54bcdc17ec24ef6c51a1fc81729a5c68d9b38658bc0afbc598'
  end

  resource 'binaryornot' do
    url 'https://files.pythonhosted.org/packages/a7/fe/7ebfec74d49f97fc55cd38240c7a7d08134002b1e14be8c3897c0dd5e49b/binaryornot-0.4.4.tar.gz'
    sha256 '359501dfc9d40632edc9fac890e19542db1a287bbcfa58175b66658392018061'
  end

  resource 'blessed' do
    url 'https://files.pythonhosted.org/packages/25/ae/92e9968ad23205389ec6bd82e2d4fca3817f1cdef34e10aa8d529ef8b1d7/blessed-1.20.0.tar.gz'
    sha256 '2cdd67f8746e048f00df47a2880f4d6acbcdb399031b604e34ba8f71d5787680'
  end

  resource 'certifi' do
    url 'https://files.pythonhosted.org/packages/b0/ee/9b19140fe824b367c04c5e1b369942dd754c4c5462d5674002f75c4dedc1/certifi-2024.8.30.tar.gz'
    sha256 'bec941d2aa8195e248a60b31ff9f0558284cf01a52591ceda73ea9afffd69fd9'
  end

  resource 'chardet' do
    url 'https://files.pythonhosted.org/packages/f3/0d/f7b6ab21ec75897ed80c17d79b15951a719226b9fababf1e40ea74d69079/chardet-5.2.0.tar.gz'
    sha256 '1b3b6ff479a8c414bc3fa2c0852995695c4a026dcd6d0633b2dd092ca39c1cf7'
  end

  resource 'charset-normalizer' do
    url 'https://files.pythonhosted.org/packages/f2/4f/e1808dc01273379acc506d18f1504eb2d299bd4131743b9fc54d7be4df1e/charset_normalizer-3.4.0.tar.gz'
    sha256 '223217c3d4f82c3ac5e29032b3f1c2eb0fb591b72161f86d93f5719079dae93e'
  end

  resource 'click' do
    url 'https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz'
    sha256 'ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de'
  end

  resource 'cookiecutter' do
    url 'https://files.pythonhosted.org/packages/52/17/9f2cd228eb949a91915acd38d3eecdc9d8893dde353b603f0db7e9f6be55/cookiecutter-2.6.0.tar.gz'
    sha256 'db21f8169ea4f4fdc2408d48ca44859349de2647fbe494a9d6c3edfc0542c21c'
  end

  resource 'editor' do
    url 'https://files.pythonhosted.org/packages/2a/92/734a4ab345914259cb6146fd36512608ea42be16195375c379046f33283d/editor-1.6.6.tar.gz'
    sha256 'bb6989e872638cd119db9a4fce284cd8e13c553886a1c044c6b8d8a160c871f8'
  end

  resource 'idna' do
    url 'https://files.pythonhosted.org/packages/f1/70/7703c29685631f5a7590aa73f1f1d3fa9a380e654b86af429e0934a32f7d/idna-3.10.tar.gz'
    sha256 '12f65c9b470abda6dc35cf8e63cc574b1c52b11df2c86030af0ac09b01b13ea9'
  end

  resource 'inquirer' do
    url 'https://files.pythonhosted.org/packages/f3/06/ef91eb8f3feafb736aa33dcb278fc9555d17861aa571b684715d095db24d/inquirer-3.4.0.tar.gz'
    sha256 '8edc99c076386ee2d2204e5e3653c2488244e82cb197b2d498b3c1b5ffb25d0b'
  end

  resource 'Jinja2' do
    url 'https://files.pythonhosted.org/packages/ed/55/39036716d19cab0747a5020fc7e907f362fbf48c984b14e62127f7e68e5d/jinja2-3.1.4.tar.gz'
    sha256 '4a3aee7acbbe7303aede8e9648d13b8bf88a429282aa6122a993f0ac800cb369'
  end

  resource 'markdown-it-py' do
    url 'https://files.pythonhosted.org/packages/38/71/3b932df36c1a044d397a1f92d1cf91ee0a503d91e470cbd670aa66b07ed0/markdown-it-py-3.0.0.tar.gz'
    sha256 'e3f60a94fa066dc52ec76661e37c851cb232d92f9886b15cb560aaada2df8feb'
  end

  resource 'MarkupSafe' do
    url 'https://files.pythonhosted.org/packages/b2/97/5d42485e71dfc078108a86d6de8fa46db44a1a9295e89c5d6d4a06e23a62/markupsafe-3.0.2.tar.gz'
    sha256 'ee55d3edf80167e48ea11a923c7386f4669df67d7994554387f84e7d8b0a2bf0'
  end

  resource 'mdurl' do
    url 'https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz'
    sha256 'bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba'
  end

  resource 'Pygments' do
    url 'https://files.pythonhosted.org/packages/8e/62/8336eff65bcbc8e4cb5d05b55faf041285951b6e80f33e2bff2024788f31/pygments-2.18.0.tar.gz'
    sha256 '786ff802f32e91311bff3889f6e9a86e81505fe99f2735bb6d60ae0c5004f199'
  end

  resource 'python-dateutil' do
    url 'https://files.pythonhosted.org/packages/66/c0/0c8b6ad9f17a802ee498c46e004a0eb49bc148f2fd230864601a86dcf6db/python-dateutil-2.9.0.post0.tar.gz'
    sha256 '37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3'
  end

  resource 'python-slugify' do
    url 'https://files.pythonhosted.org/packages/87/c7/5e1547c44e31da50a460df93af11a535ace568ef89d7a811069ead340c4a/python-slugify-8.0.4.tar.gz'
    sha256 '59202371d1d05b54a9e7720c5e038f928f45daaffe41dd10822f3907b937c856'
  end

  resource 'PyYAML' do
    url 'https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz'
    sha256 'd584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e'
  end

  resource 'readchar' do
    url 'https://files.pythonhosted.org/packages/18/31/2934981710c63afa9c58947d2e676093ce4bb6c7ce60aac2fcc4be7d98d0/readchar-4.2.0.tar.gz'
    sha256 '44807cbbe377b72079fea6cba8aa91c809982d7d727b2f0dbb2d1a8084914faa'
  end

  resource 'requests' do
    url 'https://files.pythonhosted.org/packages/63/70/2bf7780ad2d390a8d301ad0b550f1581eadbd9a20f896afe06353c2a2913/requests-2.32.3.tar.gz'
    sha256 '55365417734eb18255590a9ff9eb97e9e1da868d4ccd6402399eaf68af20a760'
  end

  resource 'rich' do
    url 'https://files.pythonhosted.org/packages/92/76/40f084cb7db51c9d1fa29a7120717892aeda9a7711f6225692c957a93535/rich-13.8.1.tar.gz'
    sha256 '8260cda28e3db6bf04d2d1ef4dbc03ba80a824c88b0e7668a0f23126a424844a'
  end

  resource 'ruamel.yaml' do
    url 'https://files.pythonhosted.org/packages/29/81/4dfc17eb6ebb1aac314a3eb863c1325b907863a1b8b1382cdffcb6ac0ed9/ruamel.yaml-0.18.6.tar.gz'
    sha256 '8b27e6a217e786c6fbe5634d8f3f11bc63e0f80f6a5890f28863d9c45aac311b'
  end

  resource 'ruamel.yaml.clib' do
    url 'https://files.pythonhosted.org/packages/46/ab/bab9eb1566cd16f060b54055dd39cf6a34bfa0240c53a7218c43e974295b/ruamel.yaml.clib-0.2.8.tar.gz'
    sha256 'beb2e0404003de9a4cab9753a8805a8fe9320ee6673136ed7f04255fe60bb512'
  end

  resource 'runs' do
    url 'https://files.pythonhosted.org/packages/26/6d/b9aace390f62db5d7d2c77eafce3d42774f27f1829d24fa9b6f598b3ef71/runs-1.2.2.tar.gz'
    sha256 '9dc1815e2895cfb3a48317b173b9f1eac9ba5549b36a847b5cc60c3bf82ecef1'
  end

  resource 'shellingham' do
    url 'https://files.pythonhosted.org/packages/58/15/8b3609fd3830ef7b27b655beb4b4e9c62313a4e8da8c676e142cc210d58e/shellingham-1.5.4.tar.gz'
    sha256 '8dbca0739d487e5bd35ab3ca4b36e11c4078f3a234bfce294b0a0291363404de'
  end

  resource 'six' do
    url 'https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz'
    sha256 '1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926'
  end

  resource 'text-unidecode' do
    url 'https://files.pythonhosted.org/packages/ab/e2/e9a00f0ccb71718418230718b3d900e71a5d16e701a3dae079a21e9cd8f8/text-unidecode-1.3.tar.gz'
    sha256 'bad6603bb14d279193107714b288be206cac565dfa49aa5b105294dd5c4aab93'
  end

  resource 'toml' do
    url 'https://files.pythonhosted.org/packages/be/ba/1f744cdc819428fc6b5084ec34d9b30660f6f9daaf70eead706e3203ec3c/toml-0.10.2.tar.gz'
    sha256 'b3bda1d108d5dd99f4a20d24d9c348e91c4db7ab1b749200bded2f839ccbe68f'
  end

  resource 'typer' do
    url 'https://files.pythonhosted.org/packages/c5/58/a79003b91ac2c6890fc5d90145c662fd5771c6f11447f116b63300436bc9/typer-0.12.5.tar.gz'
    sha256 'f592f089bedcc8ec1b974125d64851029c3b1af145f04aca64d69410f0c9b722'
  end

  resource 'types-python-dateutil' do
    url 'https://files.pythonhosted.org/packages/31/f8/f6ee4c803a7beccffee21bb29a71573b39f7037c224843eff53e5308c16e/types-python-dateutil-2.9.0.20241003.tar.gz'
    sha256 '58cb85449b2a56d6684e41aeefb4c4280631246a0da1a719bdbe6f3fb0317446'
  end

  resource 'typing-extensions' do
    url 'https://files.pythonhosted.org/packages/df/db/f35a00659bc03fec321ba8bce9420de607a1d37f8342eee1863174c69557/typing_extensions-4.12.2.tar.gz'
    sha256 '1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8'
  end

  resource 'urllib3' do
    url 'https://files.pythonhosted.org/packages/ed/63/22ba4ebfe7430b76388e7cd448d5478814d3032121827c12a2cc287e2260/urllib3-2.2.3.tar.gz'
    sha256 'e7d814a81dad81e6caf2ec9fdedb284ecc9c73076b62654547cc64ccdcae26e9'
  end

  resource 'wcwidth' do
    url 'https://files.pythonhosted.org/packages/6c/63/53559446a878410fc5a5974feb13d31d78d752eb18aeba59c7fef1af7598/wcwidth-0.2.13.tar.gz'
    sha256 '72ea0c06399eb286d978fdedb6923a9eb47e1c486ce63e9b4e64fc18303972b5'
  end

  resource 'xmod' do
    url 'https://files.pythonhosted.org/packages/72/b2/e3edc608823348e628a919e1d7129e641997afadd946febdd704aecc5881/xmod-1.8.1.tar.gz'
    sha256 '38c76486b9d672c546d57d8035df0beb7f4a9b088bc3fb2de5431ae821444377'
  end

  def install
    ENV.append_to_cflags '-Wno-incompatible-function-pointer-types' if DevelopmentTools.clang_build_version >= 1500
    virtualenv_install_with_resources
  end

  test do
    system bin / 'agentstack', '--help'
  end
end
