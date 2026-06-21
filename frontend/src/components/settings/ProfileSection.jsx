import React, { useState } from 'react';
import { UserCircle2, Upload, Save } from 'lucide-react';
import { toast } from 'sonner';
import { userProfile } from '../../mock/mockData';

const ProfileSection = () => {
  const [form, setForm] = useState({
    fullName: userProfile.fullName,
    email: userProfile.email,
    phone: userProfile.phone,
    company: userProfile.company,
  });

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSave = (e) => {
    e.preventDefault();
    toast.success('Profil sauvegardé');
  };

  return (
    <section className="zy-card rounded-2xl p-6 lg:p-8">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-xl zy-tile flex items-center justify-center flex-shrink-0">
          <UserCircle2 className="w-5 h-5 text-[#2952a3] dark:text-[#d4b78c]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Profile Information</h2>
          <p className="text-sm text-muted-foreground">Mettez à jour vos informations personnelles</p>
        </div>
      </div>

      {/* Avatar */}
      <div className="flex items-center gap-5 mb-6">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#1e3a8a] to-[#2952a3] text-white text-2xl font-bold flex items-center justify-center shadow-lg">
          {userProfile.initials}
        </div>
        <div>
          <button
            type="button"
            onClick={() => toast.info('Upload de photo mocké')}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-xl border border-border bg-secondary hover:bg-muted text-sm font-medium transition"
          >
            <Upload className="w-4 h-4" />
            Upload Photo
          </button>
          <p className="text-xs text-muted-foreground mt-2">JPG, PNG ou GIF. Max 10 MB</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Field label="Nom complet" name="fullName" value={form.fullName} onChange={onChange} />
        <Field label="Adresse e-mail" name="email" type="email" value={form.email} onChange={onChange} />
        <Field label="Téléphone" name="phone" value={form.phone} onChange={onChange} placeholder="+33 6 00 00 00 00" />
        <Field label="Entreprise" name="company" value={form.company} onChange={onChange} placeholder="Votre entreprise..." />

        <div className="md:col-span-2">
          <button
            type="submit"
            className="zy-btn-primary inline-flex items-center gap-2 h-11 px-5 rounded-xl text-sm font-medium transition"
          >
            <Save className="w-4 h-4" />
            Sauvegarder le profil
          </button>
        </div>
      </form>
    </section>
  );
};

const Field = ({ label, name, type = 'text', value, onChange, placeholder }) => (
  <label className="block">
    <span className="text-xs font-medium text-muted-foreground mb-1.5 block">{label}</span>
    <input
      type={type}
      name={name}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="zy-input w-full h-11 px-4 rounded-xl text-sm transition"
    />
  </label>
);

export default ProfileSection;
