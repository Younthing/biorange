import subprocess

def test_biorange_prints_helloworld():
    result = subprocess.run(['python', '-m', 'biorange'], capture_output=True, text=True)
    assert result.stdout.strip() == "helloworld"
