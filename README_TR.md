# 🚀 PM2 Python Kütüphanesi

## PM2 Süreç Yöneticisi için Profesyonel Python Wrapper

[![PyPI version](https://badge.fury.io/py/pm2.svg)](https://badge.fury.io/py/pm2)
[![Python Support](https://img.shields.io/pypi/pyversions/pm2.svg)](https://pypi.org/project/pm2/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Downloads](https://pepy.tech/badge/pm2)](https://pepy.tech/project/pm2)

**🔥 [Proje Ana Sayfası](https://projects.yakupkaya.me/pm2) | 📚 [Tam Dokümantasyon](https://docs.yakupkaya.me/pm2)**

---

> **⚠️ ÖNEMLİ:** Bu proje **Ocak 2024'ten beri ilk büyük güncellemesini aldı** ve **sıfırdan tamamen yeniden yazıldı**. Önceki hatalı sürüm tamamen yeniden tasarlandı ve önemli ölçüde geliştirildi. En güncel bilgiler için lütfen **[yeni dokümantasyon sitesine](https://docs.yakupkaya.me/pm2)** bakın.

**🌍 Dil:** [🇺🇸 English](README.md) | [🇹🇷 Türkçe](README_TR.md)

### ✨ Genel Bakış

**[PM2 Süreç Yöneticisi](https://pm2.keymetrics.io/)** ile kusursuz entegrasyon sağlayan güçlü, üretime hazır Python kütüphanesi. **PM2**, Node.js uygulamaları için endüstri standardı haline gelmiş, binlerce şirket tarafından üretim ortamlarında güvenilir şekilde kullanılan, savaş testinden geçmiş bir süreç yöneticisidir. Bu Python wrapper'ı, PM2'nin kurumsal düzeydeki süreç yönetimi gücünü doğrudan Python uygulamalarınıza ve betiklerinize getirir.

Python'un güvenilirliği ve esnekliği ile süreçleri programatik olarak kontrol etmesi gereken geliştiriciler ve sistem yöneticileri için özel olarak tasarlanmıştır.

**🎯 Mükemmel kullanım alanları:** Web uygulamaları, mikroservisler, arka plan görevleri, veri işleme hatları ve üretim dağıtımları.

### 🚨 Yeni Sürüm Bildirimi

Bu kütüphane **Ocak 2024'ten beri ilk büyük güncellemesini aldı** ve önceki sürümdeki tüm sorunları gidermek için **sıfırdan tamamen yeniden yazıldı**. Yeni sürüm şunları içerir:

- Modern Python uygulamaları ile **tam kod yeniden yazımı**
- **Gelişmiş güvenilirlik** ve hata yönetimi
- **[docs.yakupkaya.me/pm2](https://docs.yakupkaya.me/pm2)** adresinde **kapsamlı dokümantasyon**
- **[projects.yakupkaya.me/pm2](https://projects.yakupkaya.me/pm2)** adresinde **profesyonel proje sayfası**

### 🚀 Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| **🔄 Kapsamlı Süreç Kontrolü** | Süreçleri başlatma, durdurma, yeniden başlatma, yeniden yükleme ve silme |
| **⚡ Async & Sync Desteği** | Hem senkron hem de asenkron arayüzler |
| **📊 Gerçek Zamanlı İzleme** | CPU, bellek, çalışma süresi ve performans metrikleri |
| **🛡️ Üretime Hazır** | Kapsamlı hata yönetimi ve sağlam mimari |
| **🔧 Esnek Yapılandırma** | Ortam değişkenleri, özel ayarlar ve dağıtım seçenekleri |
| **📝 Zengin Süreç Bilgisi** | Günlükler, durum ve sağlık metrikleri dahil detaylı görüşler |

### 📖 Dokümantasyon

**👆 Lütfen eksiksiz bilgi için ana dokümantasyon sitemizi ziyaret edin:**

- **🌟 [Proje Ana Sayfası](https://projects.yakupkaya.me/pm2)** - Resmi proje sayfası
- **🏠 [Ana Dokümantasyon](https://docs.yakupkaya.me/pm2)** - Kapsamlı kılavuz ve öğreticiler
- **🔥 [Örnekler](https://projects.yakupkaya.me/pm2/examples.html)** - Pratik kod örnekleri
- **⚙️ [Gelişmiş Kullanım](https://projects.yakupkaya.me/pm2/advanced-usage.html)** - Gelişmiş kalıplar ve yapılandırmalar
- **🔧 [Sorun Giderme](https://projects.yakupkaya.me/pm2/troubleshooting.html)** - Yaygın sorunlara çözümler

### 📦 Kurulum

```bash
# PyPI'dan kurulum (önerilen)
pip install pm2

# Veya kaynaktan kurulum
git clone https://github.com/y4kupkaya/PM2.git
cd PM2
pip install -e .
```

### ⚡ Hızlı Başlangıç

```python
from pm2 import PM2Manager

# PM2 yöneticisini başlat
pm2 = PM2Manager()

# Bir süreç başlat
process = pm2.start_app(
    script="app.py",
    name="benim-uygulamam",
    env={"PORT": "3000"}
)

# Süreci izle
print(f"Durum: {process.status}")
print(f"CPU: {process.metrics.cpu}%")
print(f"Bellek: {process.metrics.memory_mb} MB")

# Tüm süreçleri listele
for proc in pm2.list_processes():
    print(f"{proc.name}: {proc.status}")
```

### 🌟 Neden PM2 Python Kütüphanesini Seçmelisiniz?

- **🎯 Üretime Hazır** - Üretim ortamlarında savaş testi geçmiş
- **📈 Yüksek Performans** - Minimal ek yük için optimize edilmiş
- **🔒 Tip Güvenli** - Tam tip ipuçları ve mypy uyumluluğu
- **🧪 İyi Test Edilmiş** - %95+ kapsama ile kapsamlı test paketi
- **📚 Harika Dokümantasyon** - Gerçek dünya örnekleri ile kapsamlı dokümanlar

---

## 📋 Ön Gereksinimler

**PM2** sisteminizde kurulu olmalıdır. PM2, Microsoft, IBM ve Netflix gibi şirketler tarafından kritik üretim iş yüklerini yönetmek için güvenilen, Node.js uygulamaları için dünyanın en popüler üretim süreç yöneticisidir.

```bash
# PM2'yi global olarak kurun
npm install -g pm2

# Kurulumu doğrulayın
pm2 --version
```

**PM2 Hakkında:** PM2 (Process Manager 2), Node.js uygulamaları için gelişmiş, üretim sınıfı bir çalışma zamanı ve süreç yöneticisidir. Otomatik yeniden başlatmalar, yük dengeleme, bellek izleme ve sorunsuz dağıtımlar gibi özellikler sağlar. Daha fazla bilgi için [pm2.keymetrics.io](https://pm2.keymetrics.io/) adresini ziyaret edin.

## 🔧 Gelişmiş Kullanım

Gelişmiş kalıplar, asenkron işlemler, üretim dağıtımları ve karmaşık yapılandırmalar için **[Gelişmiş Kullanım Kılavuzumuzu](https://projects.yakupkaya.me/pm2/advanced-usage.html)** ziyaret edin.

## 🐛 Sorun Giderme

Sorunlarla mı karşılaştınız? Yaygın sorunlara çözümler için **[Sorun Giderme Kılavuzumuzu](https://projects.yakupkaya.me/pm2/troubleshooting.html)** kontrol edin.

## 🤝 Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Detaylar için lütfen **[Katkı Yönergelerimizi](CONTRIBUTING.md)** inceleyin.

1. Repository'yi fork edin
2. Özellik branch'inizi oluşturun (`git checkout -b feature/harika-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Harika özellik ekle'`)
4. Branch'inizi push edin (`git push origin feature/harika-ozellik`)
5. Bir Pull Request açın

## 📄 Lisans

Bu proje **GNU Genel Kamu Lisansı v3.0** altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- **PM2 Ekibi** - Harika PM2 süreç yöneticisini yarattığınız için
- **Topluluk Katkıda Bulunanları** - Değerli katkılarınız için teşekkür ederiz
- **Kullanıcılar** - Bu kütüphaneyi daha iyi hale getirmek için test ettiğiniz ve geri bildirim sağladığınız için

## 📞 Destek

- 🌟 [Proje Ana Sayfası](https://projects.yakupkaya.me/pm2)
- 📚 [Dokümantasyon](https://docs.yakupkaya.me/pm2)
- 🐛 [Sorun Takipçisi](https://github.com/y4kupkaya/PM2/issues)
- 📧 [Sahip WebSitesi](https://yakupkaya.me)

---

**❤️ ile [Yakup Kaya](https://yakupkaya.me) tarafından yapıldı**