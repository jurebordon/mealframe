'use client'

/**
 * Meals Library page.
 *
 * Currently supports CSV import. Full CRUD is a separate ROADMAP task.
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Upload } from 'lucide-react'
import { CSVImporter } from '@/components/mealframe/csv-importer'

export default function MealsPage() {
  const [importOpen, setImportOpen] = useState(false)

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 pb-24 pt-safe">
        <header className="mb-8 pt-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Meals Library
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse, add, edit, and import meals
            </p>
          </div>
          <Button onClick={() => setImportOpen(true)} variant="outline" className="gap-2">
            <Upload className="h-4 w-4" />
            Import CSV
          </Button>
        </header>

        <section className="rounded-xl border border-border bg-card p-6">
          <p className="text-sm text-muted-foreground">
            Meal list and CRUD operations coming soon. Use the Import CSV button above to bulk import meals from a CSV file.
          </p>
        </section>
      </div>

      <CSVImporter
        open={importOpen}
        onOpenChange={setImportOpen}
      />
    </main>
  )
}
