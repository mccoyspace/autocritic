# Sample Images

CC0 public domain images from The Metropolitan Museum of Art's Open Access collection. These are provided so users can test autocritic without needing their own images.

| File | Artist | Medium | Period |
|------|--------|--------|--------|
| `Cozens.jpg` | Alexander Cozens | Ink wash landscape | 18th c. |
| `Friedrich.jpg` | Caspar David Friedrich | Oil painting, moonlit landscape | 19th c. |
| `Goltzius.jpg` | Hendrick Goltzius | Engraving (Hercules) | 16th c. |
| `Hiroshige.jpg` | Utagawa Hiroshige | Woodblock print, rain scene | 19th c. |
| `Whistler.jpg` | James McNeill Whistler | Etching, street scene | 19th c. |

## License

These images are in the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Source: [The Met Open Access](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access).

## Usage

```bash
# Critique a sample image
python3 -m autocritic critique tests/fixtures/samples/Friedrich.jpg --critic wolfflin

# Try different critics
python3 -m autocritic critique tests/fixtures/samples/Hiroshige.jpg --critic kandinsky
python3 -m autocritic critique tests/fixtures/samples/Goltzius.jpg --critic ruskin
```
