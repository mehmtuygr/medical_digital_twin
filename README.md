# Medikal Dijital İkiz Projesi

Bu proje, DICOM formatındaki tıbbi görüntü kesitlerini işleyerek hastaya ait medikal görüntü verilerinden üç boyutlu bir dijital temsil oluşturmayı amaçlayan eğitim amaçlı bir medikal dijital ikiz prototipidir. Sistem, DICOM serilerinden elde edilen 2 boyutlu kesitleri doğru sırayla birleştirerek 3 boyutlu hacim verisi üretir ve bu hacim üzerinden Marching Cubes algoritması ile yüzey modeli çıkarır.

Geliştirilen uygulama, tıbbi görüntülerin yalnızca 2 boyutlu kesitler halinde incelenmesi yerine, hacimsel olarak analiz edilmesine ve interaktif 3D model şeklinde görüntülenmesine olanak sağlar. Böylece kullanıcı, medikal görüntü verisini axial, coronal ve sagittal düzlemlerde inceleyebilir; aynı zamanda oluşturulan 3D dijital ikiz modelini farklı açılardan değerlendirebilir.

Projede derin öğrenme veya makine öğrenmesi kullanılmamıştır. Bunun yerine DICOM okuma, metadata tabanlı kesit sıralama, Hounsfield Unit dönüşümü, windowing, normalizasyon, opsiyonel filtreleme, hacim oluşturma, 3D rekonstrüksiyon, görselleştirme ve STL/OBJ formatında dışa aktarma gibi klasik medikal görüntü işleme adımları uygulanmıştır.

## Proje Yapısı

```text
medical-digital-twin/
│
├── app.py
├── requirements.txt
├── README.md
│
├── src/
│   ├── dicom_loader.py
│   ├── preprocessing.py
│   ├── volume_builder.py
│   ├── visualization_2d.py
│   ├── reconstruction_3d.py
│   ├── digital_twin.py
│   └── export_model.py
│
└── sample_data/
    └── README.md
```

## Çalıştırma

Proje klasöründe aşağıdaki komutu çalıştırın:

```bash
streamlit run app.py
```

Komuttan sonra uygulama tarayıcıda açılır.

## Kullanım

Sol paneldeki `DICOM klasör yolu` alanına DICOM dosyalarının bulunduğu klasör yolu yazılır.

Bu proje için örnek veri seti olarak Kaggle üzerindeki Cranial CT veri seti kullanılabilir:

```text
https://www.kaggle.com/datasets/abbymorgan/cranial-ct
```

Veri seti indirildikten sonra DICOM dosyalarının bulunduğu klasör yolu uygulamaya girilmelidir.

Uygulama önce `.dcm` uzantılı dosyaları okur. Eğer `.dcm` dosyası bulunamazsa klasördeki diğer dosyalar da DICOM olabilir diye denenir.
